#!/usr/bin/env python3
"""
Adversarial code reviewer — multi-provider (OpenAI / Anthropic).
Reviews source code across 7 sequential topics with multi-turn conversation.

Commands:
    review       Start a fresh review for a specific topic. Returns issues JSON.
    respond      Continue conversation within a topic (inner loop exchange).
    consensus    Request final consensus summary for a topic.
    check-config Verify configuration and API key.

Topic Model:
    The reviewer evaluates code across 7 sequential topics:
        1. Architecture      — system responsibilities and boundaries
        2. Code Structure    — class layout, function organization, coupling
        3. Simulation Design — pipeline robustness, edge cases, state machines
        4. Performance       — scaling, tick cost, hot paths
        5. Project Org       — file placement, repo conventions
        6. Engine Correctness — memory, signals, node lifecycle (Godot/GDExtension)
        7. Maintainability   — long-term health, readability, growth resilience

    Each topic gets its own review → respond → consensus cycle.
    The --iterate option repeats all 7 topics on the updated code.

Conversation state is saved to .reviews/ so exchanges can continue across calls.
No pip dependencies — uses urllib only.

Environment:
    OPENAI_API_KEY or ANTHROPIC_API_KEY — set via .env file in project root or env var.
"""

import json
import os
import sys
import argparse
import hashlib
import re
import time
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration & Auth
# ---------------------------------------------------------------------------

def load_config(profile=None):
    """Load review_config.json, optionally merging a named profile.

    Uses the same config file as adversarial-review.py — both reviewers share
    provider settings, temperature, and token limits. Profiles (e.g.,
    "code_review") override provider/model settings from the top level.
    """
    config_path = Path(__file__).parent / "review_config.json"
    if not config_path.exists():
        print(json.dumps({"error": "review_config.json not found", "path": str(config_path)}))
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        base_config = json.load(f)

    if not profile or profile not in base_config:
        return base_config

    profile_config = base_config[profile]
    merged = dict(base_config)
    if "provider" in profile_config:
        merged["provider"] = profile_config["provider"]
    if "fallback_order" in profile_config:
        merged["fallback_order"] = profile_config["fallback_order"]
    for provider_name in ["openai", "anthropic", "google"]:
        if provider_name in profile_config:
            if provider_name not in merged:
                merged[provider_name] = {}
            for key, val in profile_config[provider_name].items():
                merged[provider_name][key] = val
    return merged


def get_api_key(config):
    """Resolve API key from environment variable or .env file.

    Checks (in order):
        1. Environment variable (e.g., OPENAI_API_KEY)
        2. scaffold/.env file (key=value pairs)
    """
    provider = config.get("provider", "openai")
    provider_config = config.get(provider, {})
    env_var = provider_config.get("api_key_env", "OPENAI_API_KEY")

    key = os.environ.get(env_var)

    if not key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k == env_var:
                    key = v
                    break

    if not key:
        print(json.dumps({
            "error": "API key not found",
            "provider": provider,
            "checked": [f"Environment variable: {env_var}", ".env file in scaffold root"],
            "fix": f"Set {env_var} in your environment or create scaffold/.env with:\n{env_var}=your-key-here"
        }))
        sys.exit(1)
    return key


# ---------------------------------------------------------------------------
# Conversation State
# ---------------------------------------------------------------------------

def get_conv_dir():
    """Get or create .reviews/ directory for conversation state."""
    conv_dir = Path(__file__).parent.parent / ".reviews"
    conv_dir.mkdir(exist_ok=True)
    return conv_dir


def conv_path(code_path, topic, iteration):
    """Path to conversation state file for a code file + topic + iteration.

    Format: conv-code-{filename}-{hash}-topic{N}-iter{M}.json
    The hash prevents collisions when files in different directories share names.
    """
    code_hash = hashlib.md5(str(code_path).encode()).hexdigest()[:8]
    code_name = Path(code_path).stem
    return get_conv_dir() / f"conv-code-{code_name}-{code_hash}-topic{topic}-iter{iteration}.json"


def save_conversation(path, data):
    """Save conversation state to disk."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_conversation(path):
    """Load conversation state from disk. Returns None if not found."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Topic Definitions
# ---------------------------------------------------------------------------
# Each topic defines what the reviewer should focus on. Sub-points guide
# the review toward specific concerns. Criteria define what "good" looks like.

TOPICS = {
    1: {
        "name": "Architecture",
        "description": "System responsibilities and boundary analysis",
        "sub_points": [
            "Whether the system's responsibilities are appropriate for a single class",
            "If system boundaries match the project's architectural model (domain systems + managers + orchestrator)",
            "If anything should be split into smaller systems or merged with existing ones",
            "Dependency count and coupling assessment — does this system depend on too many siblings?",
            "Whether the system is doing work that belongs to another system",
        ],
        "criteria": [
            "Single responsibility — the system has one clear domain purpose",
            "Dependency hygiene — dependencies are justified and minimal",
            "Boundary clarity — it is obvious what belongs here vs. in another system",
            "Authority compliance — data ownership follows the project's authority table",
            "Growth trajectory — the architecture can absorb new features without becoming a God class",
        ],
    },
    2: {
        "name": "Code Structure",
        "description": "Class layout, function organization, and coupling analysis",
        "sub_points": [
            "Class layout — member ordering, section organization, header structure",
            "Function organization — are related functions grouped together?",
            "Dependency injection vs hard coupling — how are sibling systems resolved?",
            "File size and compilation unit organization — is the file too large?",
            "API surface area — is the public API intentional or sprawling?",
        ],
        "criteria": [
            "Navigability — a reader can find what they need without excessive scrolling",
            "Section discipline — related code is grouped with clear boundaries",
            "Coupling style — dependencies are resolved through a consistent pattern",
            "Compilation unit health — file size is manageable, split if needed",
            "API coherence — public methods form a logical, intentional interface",
        ],
    },
    3: {
        "name": "Simulation Design",
        "description": "Processing pipeline robustness and edge case handling",
        "sub_points": [
            "Whether the system's processing pipeline is robust and complete",
            "Edge case handling — interruptions, invalid state, missing dependencies, cancellation",
            "State machine correctness — are all transitions valid and reachable?",
            "Recovery behavior — does the system handle partial failure gracefully?",
            "Domain-specific correctness — does the simulation behavior match colony-sim expectations?",
        ],
        "criteria": [
            "Pipeline completeness — the full lifecycle is handled (create → process → complete/fail)",
            "Interruption awareness — the system handles interruption as first-class, not exceptional",
            "State integrity — no orphaned states, no impossible transitions",
            "Failure recovery — the system can recover from partial failures without manual intervention",
            "Simulation realism — behavior matches what a colony-sim player would expect",
        ],
    },
    4: {
        "name": "Performance",
        "description": "Scaling analysis and tick cost assessment",
        "sub_points": [
            "Per-tick cost at current scale and projected mid-game scale (20-40 colonists, hundreds of entities)",
            "O(n) vs O(n²) scan patterns — are there nested loops over entity arrays?",
            "Memory allocation patterns — heap churn, cache friendliness, fixed vs dynamic arrays",
            "Hot paths and early exit opportunities — is cheap work skipped early?",
            "Pathfinding and spatial query frequency — are expensive operations triggered appropriately?",
        ],
        "criteria": [
            "Tick budget — per-tick cost stays within budget at projected scale",
            "Scan efficiency — no unnecessary nested scans over large arrays",
            "Allocation discipline — no per-tick heap allocations in hot paths",
            "Early exits — inactive/irrelevant entities are skipped cheaply",
            "Expensive operations — pathfinding, global searches, etc. are event-driven, not polled",
        ],
    },
    5: {
        "name": "Project Organization",
        "description": "File placement, naming, and repo structure",
        "sub_points": [
            "Whether code belongs in this system or somewhere else in the repo layout",
            "File naming conventions — does the name match the class and its purpose?",
            "Header/implementation separation — is the split clean?",
            "Build system integration — will SCons/CMake pick up new files correctly?",
            "Multi-file class organization — if the class spans multiple .cpp files, is the split logical?",
        ],
        "criteria": [
            "Discoverability — a new contributor can find the code based on its name and location",
            "Convention compliance — naming follows the project's established patterns",
            "Build integration — new files are automatically discovered by the build system",
            "Logical grouping — related files live near each other",
            "Split rationale — if the class spans multiple files, the split follows domain boundaries",
        ],
    },
    6: {
        "name": "Engine Correctness",
        "description": "Godot 4 / GDExtension pattern compliance",
        "sub_points": [
            "Memory management — no leaks, proper ownership, no dangling pointers",
            "Signal use — registration in _bind_methods(), proper emission, correct parameter types",
            "Node lifecycle usage — _ready() for initialization, correct tick pattern",
            "ClassDB binding correctness — all exposed methods/properties properly bound",
            "GDExtension-specific patterns — GDCLASS macro, sibling resolution, cast_to<T> usage",
        ],
        "criteria": [
            "Memory safety — no leaks or dangling references under normal operation",
            "Signal correctness — signals are registered, emitted with correct signatures, connectable from GDScript",
            "Lifecycle compliance — initialization happens in _ready(), not constructor; tick is properly managed",
            "Binding completeness — everything exposed to GDScript is properly bound in _bind_methods()",
            "Pattern consistency — GDExtension patterns match the project's established conventions",
        ],
    },
    7: {
        "name": "Maintainability",
        "description": "Long-term health, readability, and growth resilience",
        "sub_points": [
            "Whether this system will become spaghetti as the project grows (40-60 systems)",
            "Comment quality — are comments helpful, accurate, and sufficient for a non-developer reader?",
            "Debugging friendliness — can a developer trace problems through this code efficiently?",
            "Diagnostic instrumentation — are there [DIAG] warnings at key decision points?",
            "Growth patterns — what happens when new features are added to this system?",
        ],
        "criteria": [
            "Readability — a developer unfamiliar with this system can understand it in one pass",
            "Comment density — non-trivial logic is explained; comments describe why, not just what",
            "Debug-ability — errors produce clear messages; state is inspectable",
            "Extensibility — adding a new feature type doesn't require touching unrelated code",
            "Complexity trajectory — the system's complexity grows linearly with features, not exponentially",
        ],
    },
}


# ---------------------------------------------------------------------------
# Rate Limit Retry Helper
# ---------------------------------------------------------------------------

# Maximum number of retries when hitting a rate limit (HTTP 429).
MAX_RATE_LIMIT_RETRIES = 5

# Default wait time in seconds when the API doesn't tell us how long to wait.
DEFAULT_RATE_LIMIT_WAIT = 10

# Extra padding added to the API-suggested wait time to avoid hitting the
# limit again immediately after the window resets.
RATE_LIMIT_PADDING = 2


def _parse_retry_after(error_message):
    """Extract the suggested wait time from an OpenAI/Anthropic 429 error message.

    OpenAI messages look like: "...Please try again in 2.134s..."
    Anthropic messages look like: "...Please retry after X seconds..."

    Returns the number of seconds to wait, or None if unparsable.
    """
    # Match patterns like "in 2.134s" or "in 10s"
    match = re.search(r"try again in (\d+(?:\.\d+)?)s", error_message, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Match patterns like "after 10 seconds"
    match = re.search(r"after (\d+(?:\.\d+)?)\s*seconds?", error_message, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def _make_api_request(url, payload, headers, timeout=180):
    """Make an HTTP POST request with automatic retry on rate limit (429) errors.

    Returns the parsed JSON response body on success.
    Raises urllib.error.HTTPError for non-429 errors.
    Raises urllib.error.URLError for network errors.
    Returns a dict with an "error" key if retries are exhausted.
    """
    import urllib.request
    import urllib.error

    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limited — parse wait time and retry
                error_body = e.read().decode("utf-8") if e.fp else ""
                try:
                    error_json = json.loads(error_body)
                    msg = error_json.get("error", {}).get("message", error_body)
                except json.JSONDecodeError:
                    msg = error_body

                wait_time = _parse_retry_after(msg)
                if wait_time is None:
                    wait_time = DEFAULT_RATE_LIMIT_WAIT
                else:
                    wait_time += RATE_LIMIT_PADDING

                if attempt < MAX_RATE_LIMIT_RETRIES:
                    # Print to stderr so the caller still gets clean JSON on stdout
                    print(
                        f"[rate-limit] 429 on attempt {attempt}/{MAX_RATE_LIMIT_RETRIES}. "
                        f"Waiting {wait_time:.1f}s before retry...",
                        file=sys.stderr,
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # Exhausted retries
                    return {"error": f"Rate limit exceeded after {MAX_RATE_LIMIT_RETRIES} retries: {msg}"}
            else:
                # Non-429 error — re-raise for the caller to handle
                raise


# ---------------------------------------------------------------------------
# API Calls — OpenAI
# ---------------------------------------------------------------------------

def call_openai(api_key, config, messages):
    """Call OpenAI API with JSON response format. Used for review and consensus."""
    import urllib.error

    provider_config = config.get("openai", {})
    model = provider_config.get("model", "gpt-4o")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": config.get("temperature", 0.3),
        "max_completion_tokens": config.get("max_tokens", 16384),
        "response_format": {"type": "json_object"},
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        body = _make_api_request(url, payload, headers)
        if "error" in body:
            return body  # Rate limit exhausted or other error from helper
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"OpenAI API error ({e.code}): {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from OpenAI response",
                "raw": content if "content" in dir() else "no content"}


def call_openai_raw(api_key, config, messages):
    """Call OpenAI API returning raw text (not JSON-forced). Used for inner loop exchanges."""
    import urllib.error

    provider_config = config.get("openai", {})
    model = provider_config.get("model", "gpt-4o")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": config.get("temperature", 0.3),
        "max_completion_tokens": config.get("max_tokens", 16384),
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        body = _make_api_request(url, payload, headers)
        if "error" in body:
            return body  # Rate limit exhausted or other error from helper
        content = body["choices"][0]["message"]["content"]
        return {"content": content}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"OpenAI API error ({e.code}): {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}


# ---------------------------------------------------------------------------
# API Calls — Anthropic
# ---------------------------------------------------------------------------

def call_anthropic(api_key, config, messages):
    """Call Anthropic Messages API with JSON response. Used for review and consensus."""
    import urllib.error

    provider_config = config.get("anthropic", {})
    model = provider_config.get("model", "claude-sonnet-4-20250514")

    # Anthropic uses a separate system param; extract from messages
    system_text = ""
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            api_messages.append(msg)

    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": config.get("max_tokens", 16384),
        "temperature": config.get("temperature", 0.3),
        "messages": api_messages,
    }
    if system_text:
        payload["system"] = system_text

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        body = _make_api_request(url, payload, headers)
        if "error" in body:
            return body  # Rate limit exhausted or other error from helper
        content = body["content"][0]["text"]
        # Try to extract JSON from response
        return _extract_json(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"Anthropic API error ({e.code}): {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}


def call_anthropic_raw(api_key, config, messages):
    """Call Anthropic Messages API returning raw text. Used for inner loop exchanges."""
    import urllib.error

    provider_config = config.get("anthropic", {})
    model = provider_config.get("model", "claude-sonnet-4-20250514")

    system_text = ""
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            api_messages.append(msg)

    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": config.get("max_tokens", 16384),
        "temperature": config.get("temperature", 0.3),
        "messages": api_messages,
    }
    if system_text:
        payload["system"] = system_text

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        body = _make_api_request(url, payload, headers)
        if "error" in body:
            return body  # Rate limit exhausted or other error from helper
        content = body["content"][0]["text"]
        return {"content": content}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"Anthropic API error ({e.code}): {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}


def _extract_json(text):
    """Extract JSON object from text that may contain markdown fences or preamble."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code fence
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {"error": "Failed to parse JSON from response", "raw": text}


# ---------------------------------------------------------------------------
# Provider Dispatch
# ---------------------------------------------------------------------------

def call_provider(api_key, config, messages, json_mode=True):
    """Route to the correct provider's API call.

    json_mode=True: forces structured JSON response (for review and consensus).
    json_mode=False: returns raw text (for inner loop exchanges).
    """
    provider = config.get("provider", "openai")
    if provider == "openai":
        if json_mode:
            return call_openai(api_key, config, messages)
        else:
            return call_openai_raw(api_key, config, messages)
    elif provider == "anthropic":
        if json_mode:
            return call_anthropic(api_key, config, messages)
        else:
            return call_anthropic_raw(api_key, config, messages)
    else:
        return {"error": f"Unknown provider: {provider}. Use 'openai' or 'anthropic'."}


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

def build_system_prompt():
    """Build the reviewer persona prompt for code review.

    The reviewer is a senior game developer with colony-sim experience,
    familiar with C++/GDExtension patterns and simulation architecture.
    """
    return """You are a senior game developer and software architect acting as an adversarial
code reviewer for a colony simulation game built with Godot 4 and GDExtension (C++).

The project follows a structured architecture:
- SimulationOrchestrator dispatches ticks to all systems in a defined order
- Systems are C++ Node subclasses using GDCLASS macro and ClassDB bindings
- Systems find siblings via get_parent()->get_node_or_null() in _ready()
- Entity storage uses fixed-size pre-allocated arrays (no dynamic allocation during ticks)
- Cross-system signals are wired in a central game_manager.gd, not inside individual systems
- Each piece of game data has exactly one owning system (single-writer rule)
- GDScript handles UI and orchestration; C++ handles all simulation logic

You are in a multi-turn conversation with the code author (an AI assistant).
- In the first message, you receive the code and a specific review topic. Provide your
  review as structured JSON.
- In subsequent messages, the author responds to your issues — agreeing, partially agreeing,
  or pushing back with project-specific context and reasoning.
- Engage substantively: accept good reasoning, push back on weak reasoning,
  acknowledge when the author makes a valid point.
- When asked for consensus, output a final JSON summary.

The author has deep context about the project's architecture, design decisions, and constraints.
When they provide project-specific justification for a design choice, evaluate the justification
on its merits rather than insisting on textbook patterns.

Always respond with valid JSON when starting a review or providing a final summary.
In discussion exchanges, you may use natural language."""


def build_review_prompt(code_content, topic_num, context="", focus=""):
    """Build the initial review prompt for a specific topic.

    Combines the topic definition, code content, and optional context/focus
    into a single prompt that guides the reviewer to evaluate one aspect.
    """
    topic = TOPICS[topic_num]

    # Build the sub-points list
    sub_points_text = "\n".join(f"  - {sp}" for sp in topic["sub_points"])

    # Build the criteria list
    criteria_text = "\n".join(f"  {i}. {c}" for i, c in enumerate(topic["criteria"], 1))

    # Build the focus instruction if provided
    focus_text = ""
    if focus:
        focus_text = f"\n\nREVIEW FOCUS: Concentrate on: {focus}\nOnly flag issues outside the focus area if they are HIGH severity."

    return f"""Review this code for Topic {topic_num}: {topic['name']}
({topic['description']})

Review sub-points — evaluate each of these:
{sub_points_text}

Evaluation criteria — what "good" looks like:
{criteria_text}

OUT OF SCOPE for this topic:
- Issues that belong to other topics (those will be reviewed separately)
- Hypothetical future problems that have no current evidence in the code
- Style preferences that don't affect correctness, performance, or maintainability
{f"{chr(10)}Additional context:{chr(10)}{context}" if context else ""}
{focus_text}

Respond with a JSON object:
{{
    "topic": {topic_num},
    "topic_name": "{topic['name']}",
    "summary": "1-2 sentence overall assessment for this topic",
    "score": "N/10 — numeric score for this topic",
    "issues": [
        {{
            "id": 1,
            "severity": "HIGH | MEDIUM | LOW",
            "location": "function name, line range, or section description",
            "problem": "what is wrong and why it matters",
            "suggestion": "specific actionable fix",
            "sub_point": "which review sub-point this relates to"
        }}
    ],
    "strengths": ["what the code does well for this topic — max 5"],
    "verdict": "one-paragraph final assessment for this topic"
}}

Be specific. Every issue needs a concrete location and actionable suggestion.
Do NOT raise issues that belong to other review topics.
An empty issues array means you found nothing wrong for this topic.
Rate on a 1-10 scale where 5 = acceptable, 7 = good, 9 = excellent.

Code:

---
{code_content}
---"""


def build_consensus_request():
    """Prompt to ask reviewer for final consensus summary after discussion."""
    return """Based on our discussion, please provide your final consensus as JSON:
{
    "consensus_reached": true | false,
    "resolved_issues": [
        {
            "id": 1,
            "original_problem": "...",
            "resolution": "agreed to fix | rejected with sound reasoning | modified approach",
            "status": "RESOLVED | REJECTED"
        }
    ],
    "changes_to_apply": [
        "specific code change 1 to make",
        "specific code change 2 to make"
    ],
    "remaining_disagreements": [],
    "final_score": "N/10 — revised score after discussion",
    "overall_assessment": "updated assessment after discussion"
}

Set consensus_reached to true if all issues are either resolved or rejected with defensible reasoning.
Only set false if a HIGH severity issue remains with genuinely inadequate reasoning for rejection.
Revise the score if the discussion revealed the code is better or worse than initially assessed."""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_review(args):
    """Start a fresh review for a specific topic. Creates conversation state.

    Reads the code file (or multiple files), sends to the reviewer with the
    topic-specific prompt, and saves the conversation state for follow-up.
    """
    config = load_config("code_review")
    api_key = get_api_key(config)

    # Validate topic number
    topic_num = args.topic
    if topic_num not in TOPICS:
        print(json.dumps({
            "error": f"Invalid topic: {topic_num}",
            "valid_topics": {k: v["name"] for k, v in TOPICS.items()},
        }))
        sys.exit(1)

    # Read primary code file
    code_path = Path(args.code_path)
    if not code_path.exists():
        print(json.dumps({"error": f"Code file not found: {code_path}"}))
        sys.exit(1)

    # Build code content — may include multiple files
    code_parts = []
    code_parts.append(f"=== File: {code_path.name} ===\n{code_path.read_text(encoding='utf-8')}")

    # Include additional files if provided (e.g., header + split implementation files)
    for extra in (args.files or []):
        extra_path = Path(extra)
        if extra_path.exists():
            code_parts.append(f"\n\n=== File: {extra_path.name} ===\n{extra_path.read_text(encoding='utf-8')}")
        else:
            code_parts.append(f"\n\n[Warning: additional file not found: {extra}]")

    code_content = "\n".join(code_parts)

    # Load context files (architecture docs, design docs, etc.)
    context_parts = []
    for cf in (args.context_files or []):
        cf_path = Path(cf)
        if cf_path.exists():
            context_parts.append(
                f"--- Context: {cf_path.name} ---\n"
                f"{cf_path.read_text(encoding='utf-8')}\n"
                f"--- End {cf_path.name} ---"
            )
        else:
            context_parts.append(f"[Warning: context file not found: {cf}]")
    context_str = "\n\n".join(context_parts) if context_parts else ""

    # Build messages
    system_msg = build_system_prompt()
    user_msg = build_review_prompt(
        code_content, topic_num, context_str,
        focus=args.focus or ""
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    result = call_provider(api_key, config, messages, json_mode=True)

    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Save conversation state
    messages.append({"role": "assistant", "content": json.dumps(result)})

    conv_state = {
        "code_path": str(code_path),
        "additional_files": args.files or [],
        "topic": topic_num,
        "topic_name": TOPICS[topic_num]["name"],
        "iteration": args.iteration,
        "exchange": 1,
        "provider": config.get("provider", "openai"),
        "model": config.get(config.get("provider", "openai"), {}).get("model", "unknown"),
        "focus": args.focus or None,
        "started": datetime.now().isoformat(),
        "messages": messages,
        "initial_review": result,
        "consensus": None,
    }

    state_path = conv_path(args.code_path, topic_num, args.iteration)
    save_conversation(state_path, conv_state)

    # Add meta to output
    result["_meta"] = {
        "code_path": str(code_path),
        "topic": topic_num,
        "topic_name": TOPICS[topic_num]["name"],
        "iteration": args.iteration,
        "exchange": 1,
        "provider": config.get("provider", "openai"),
        "model": conv_state["model"],
        "conversation_file": str(state_path),
        "issue_count": len(result.get("issues", [])),
    }

    print(json.dumps(result, indent=2))


def cmd_respond(args):
    """Continue the conversation within a topic's review.

    Loads Claude's evaluation of the reviewer's issues from a message or file,
    appends it to the conversation, and gets the reviewer's counter-response.
    """
    config = load_config("code_review")
    api_key = get_api_key(config)

    state_path = conv_path(args.code_path, args.topic, args.iteration)
    conv_state = load_conversation(state_path)

    if not conv_state:
        print(json.dumps({
            "error": f"No conversation found for topic {args.topic}, iteration {args.iteration}",
            "fix": f"Run 'review' first: python code-review.py review {args.code_path} --topic {args.topic} --iteration {args.iteration}"
        }))
        sys.exit(1)

    # Load Claude's response
    if args.message:
        claude_message = args.message
    elif args.message_file:
        msg_path = Path(args.message_file)
        if not msg_path.exists():
            print(json.dumps({"error": f"Message file not found: {msg_path}"}))
            sys.exit(1)
        claude_message = msg_path.read_text(encoding="utf-8")
    else:
        print(json.dumps({"error": "Provide --message or --message-file"}))
        sys.exit(1)

    # Append Claude's message to conversation
    conv_state["messages"].append({"role": "user", "content": claude_message})
    conv_state["exchange"] += 1

    # Call provider with full conversation history (raw text mode for discussion)
    result = call_provider(api_key, config, conv_state["messages"], json_mode=False)

    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(1)

    reviewer_response = result["content"]

    # Append reviewer's response
    conv_state["messages"].append({"role": "assistant", "content": reviewer_response})

    # Save updated state
    save_conversation(state_path, conv_state)

    output = {
        "reviewer_response": reviewer_response,
        "_meta": {
            "code_path": conv_state["code_path"],
            "topic": conv_state["topic"],
            "topic_name": conv_state["topic_name"],
            "iteration": conv_state["iteration"],
            "exchange": conv_state["exchange"],
            "total_messages": len(conv_state["messages"]),
            "conversation_file": str(state_path),
        }
    }

    print(json.dumps(output, indent=2))


def cmd_consensus(args):
    """Ask reviewer for final consensus summary after discussion on a topic.

    Appends the consensus request to the conversation, forces a JSON response,
    and saves the result.
    """
    config = load_config("code_review")
    api_key = get_api_key(config)

    state_path = conv_path(args.code_path, args.topic, args.iteration)
    conv_state = load_conversation(state_path)

    if not conv_state:
        print(json.dumps({"error": f"No conversation found for topic {args.topic}, iteration {args.iteration}"}))
        sys.exit(1)

    # Append consensus request
    conv_state["messages"].append({"role": "user", "content": build_consensus_request()})

    # Force JSON response for consensus
    result = call_provider(api_key, config, conv_state["messages"], json_mode=True)

    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Save consensus
    conv_state["messages"].append({"role": "assistant", "content": json.dumps(result)})
    conv_state["consensus"] = result
    save_conversation(state_path, conv_state)

    result["_meta"] = {
        "code_path": conv_state["code_path"],
        "topic": conv_state["topic"],
        "topic_name": conv_state["topic_name"],
        "iteration": conv_state["iteration"],
        "exchanges": conv_state["exchange"],
        "conversation_file": str(state_path),
    }

    print(json.dumps(result, indent=2))


def cmd_check_config(args):
    """Verify configuration, API key, and list available topics."""
    config = load_config("code_review")
    provider = config.get("provider", "openai")
    provider_config = config.get(provider, {})
    env_var = provider_config.get("api_key_env", "OPENAI_API_KEY")
    model = provider_config.get("model", "unknown")

    has_key = bool(os.environ.get(env_var))

    env_file = Path(__file__).parent.parent / ".env"
    has_env_file = env_file.exists()
    if not has_key and has_env_file:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == env_var and v.strip():
                has_key = True
                break

    result = {
        "config_loaded": True,
        "provider": provider,
        "model": model,
        "temperature": config.get("temperature", 0.3),
        "max_tokens": config.get("max_tokens", 16384),
        "api_key_env": env_var,
        "api_key_found": has_key,
        "api_key_source": (
            "environment variable" if os.environ.get(env_var)
            else (".env file" if has_key else "not found")
        ),
        "env_file_exists": has_env_file,
        "topics": {k: {"name": v["name"], "description": v["description"]} for k, v in TOPICS.items()},
    }

    if not has_key:
        result["warning"] = f"API key not found. Set {env_var} in your environment or create scaffold/.env with:\n{env_var}=your-key-here"

    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point — parse arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Adversarial code reviewer — 7-topic review with multi-provider support (OpenAI / Anthropic)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # review — start fresh review for a topic
    p_review = subparsers.add_parser("review", help="Start a fresh review for a specific topic")
    p_review.add_argument("code_path", help="Path to primary code file to review")
    p_review.add_argument("--topic", type=int, required=True, choices=range(1, 8),
                          help="Topic number (1-7)")
    p_review.add_argument("--iteration", type=int, default=1,
                          help="Outer loop iteration number (for --iterate mode)")
    p_review.add_argument("--files", nargs="*", default=[],
                          help="Additional code files to include (e.g., header, split impl files)")
    p_review.add_argument("--context-files", nargs="*", default=[],
                          help="Supporting context document paths (architecture.md, etc.)")
    p_review.add_argument("--focus", default="",
                          help="Narrow the review focus within this topic")

    # respond — continue conversation within a topic
    p_respond = subparsers.add_parser("respond", help="Continue conversation (send Claude's response)")
    p_respond.add_argument("code_path", help="Path to code file being reviewed")
    p_respond.add_argument("--topic", type=int, required=True, choices=range(1, 8),
                           help="Topic number (1-7)")
    p_respond.add_argument("--iteration", type=int, required=True,
                           help="Which iteration to continue")
    p_respond.add_argument("--message", default="",
                           help="Claude's response text (inline)")
    p_respond.add_argument("--message-file", default="",
                           help="File containing Claude's response")

    # consensus — request final consensus summary for a topic
    p_consensus = subparsers.add_parser("consensus", help="Request consensus summary for topic")
    p_consensus.add_argument("code_path", help="Path to code file being reviewed")
    p_consensus.add_argument("--topic", type=int, required=True, choices=range(1, 8),
                             help="Topic number (1-7)")
    p_consensus.add_argument("--iteration", type=int, required=True,
                             help="Which iteration")

    # check-config
    subparsers.add_parser("check-config", help="Verify configuration and list topics")

    args = parser.parse_args()

    if args.command == "review":
        cmd_review(args)
    elif args.command == "respond":
        cmd_respond(args)
    elif args.command == "consensus":
        cmd_consensus(args)
    elif args.command == "check-config":
        cmd_check_config(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
