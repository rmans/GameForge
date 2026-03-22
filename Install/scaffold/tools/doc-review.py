#!/usr/bin/env python3
"""
Adversarial document reviewer — multi-provider (OpenAI / Anthropic).
Supports multi-turn conversations within each review iteration.

Commands:
    review       Start a fresh review (outer loop iteration). Returns issues JSON.
    respond      Continue conversation within an iteration (inner loop exchange).
    consensus    Request final consensus summary after discussion.
    check-config Verify configuration and API key.

Conversation Model:
    Outer loop (iterations): Fresh review of the document after changes applied.
    Inner loop (exchanges):  Back-and-forth within one iteration until consensus.

    Iteration 1: review -> issues -> respond (pushback) -> respond -> ... -> consensus -> apply changes
    Iteration 2: review -> issues -> respond -> ... -> consensus -> apply changes
    ...up to max_iterations or until reviewer finds no issues.

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
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration & Auth
# ---------------------------------------------------------------------------

def load_config(profile=None):
    """Load review_config.json, optionally merging a named profile.

    Profiles (e.g., "code_review") override provider, model, and fallback_order
    settings from the top-level config. API keys are inherited from the top level.
    """
    config_path = Path(__file__).parent / "review_config.json"
    if not config_path.exists():
        print(json.dumps({"error": "review_config.json not found", "path": str(config_path)}))
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        base_config = json.load(f)

    if not profile or profile not in base_config:
        return base_config

    # Merge profile into base config — profile overrides provider/model/fallback
    profile_config = base_config[profile]
    merged = dict(base_config)
    if "provider" in profile_config:
        merged["provider"] = profile_config["provider"]
    if "fallback_order" in profile_config:
        merged["fallback_order"] = profile_config["fallback_order"]
    # Override per-provider model/max_tokens from profile
    for provider_name in ["openai", "anthropic", "google"]:
        if provider_name in profile_config:
            if provider_name not in merged:
                merged[provider_name] = {}
            # Merge profile provider settings over base, keeping api_key_env from base
            for key, val in profile_config[provider_name].items():
                merged[provider_name][key] = val
    return merged


def get_api_key(config):
    """Resolve API key from environment variable or .env file."""
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


def conv_path(doc_path, iteration):
    """Path to conversation state file for a doc + iteration."""
    doc_hash = hashlib.md5(str(doc_path).encode()).hexdigest()[:8]
    doc_name = Path(doc_path).stem
    return get_conv_dir() / f"conv-{doc_name}-{doc_hash}-iter{iteration}.json"


def save_conversation(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_conversation(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Doc Type Detection
# ---------------------------------------------------------------------------

DOC_TYPE_PATTERNS = [
    (r"design/design-doc\.md$", "design"),
    (r"design/(style-guide|color-system|ui-kit|glossary)\.md$", "style"),
    (r"design/systems/SYS-\d+", "system"),
    (r"reference/", "reference"),
    (r"engine/", "engine"),
    (r"inputs/", "input"),
    (r"phases/roadmap\.md$", "roadmap"),
    (r"phases/P\d+-", "phase"),
    (r"slices/SLICE-\d+", "slice"),
    (r"specs/SPEC-\d+", "spec"),
    (r"tasks/TASK-\d+", "task"),
]


def detect_doc_type(doc_path):
    """Detect document type from its path using scaffold conventions."""
    normalized = str(doc_path).replace("\\", "/")
    for pattern, doc_type in DOC_TYPE_PATTERNS:
        if re.search(pattern, normalized):
            return doc_type
    return None


# ---------------------------------------------------------------------------
# Review Intensity Tiers
# ---------------------------------------------------------------------------

TIERS = {
    "full": {
        "max_iterations": 5,
        "max_exchanges": 5,
        "severity_filter": None,  # All severities
        "types": ["design", "style", "system", "roadmap", "phase", "spec"],
    },
    "lite": {
        "max_iterations": 1,
        "max_exchanges": 3,
        "severity_filter": "HIGH",
        "types": ["engine", "input", "slice", "task"],
    },
    "lint": {
        "max_iterations": 1,
        "max_exchanges": 2,
        "severity_filter": "HIGH",
        "types": ["reference"],
    },
}


def get_tier(doc_type):
    """Return the tier name and config for a given doc type."""
    for tier_name, tier_config in TIERS.items():
        if doc_type in tier_config["types"]:
            return tier_name, tier_config
    # Default to lite for unknown types
    return "lite", TIERS["lite"]


# ---------------------------------------------------------------------------
# Scope & Criteria (per doc type)
# ---------------------------------------------------------------------------

DOC_TYPE_CONTEXT = {
    "design": "a game design document — the top-level description of what the game is",
    "style": "a style/visual identity document — defines art style, colors, UI components, or terminology",
    "system": "a system design document — describes player-visible behavior for one game system",
    "reference": "a reference data table — canonical data like signals, entities, resources, or balance params",
    "engine": "an engine conventions document — defines how to build in the target engine",
    "input": "an input document — defines player actions, bindings, or input philosophy",
    "roadmap": "a project roadmap — defines the full arc from start to ship with phases and milestones",
    "phase": "a phase scope gate — defines entry/exit criteria and what gets built in this phase",
    "slice": "a vertical slice contract — defines an end-to-end playable chunk that proves systems work together",
    "spec": "a behavior specification — defines atomic testable behavior for a slice",
    "task": "an implementation task — defines concrete steps to build a spec in the target engine",
}

DOC_TYPE_SCOPE = {
    "design": {
        "in_scope": [
            "Vision clarity — is the core vision specific enough to guide all downstream docs?",
            "Pillar consistency — do all sections serve the stated pillars?",
            "Loop completeness — are core, session, and meta loops defined?",
            "System index sync — does the system list match registered systems?",
            "Scope definition — what the game IS and IS NOT",
        ],
        "out_of_scope": [
            "Implementation details or engine constructs",
            "Exact numeric values (those belong in balance params)",
            "Code patterns or API usage",
        ],
    },
    "style": {
        "in_scope": [
            "Design doc alignment — does the visual identity serve the stated vision and pillars?",
            "Internal consistency — do style rules, colors, and UI components agree with each other?",
            "Glossary compliance — are canonical terms used correctly?",
        ],
        "out_of_scope": [
            "Implementation details or engine patterns",
            "Code-level concerns",
        ],
    },
    "system": {
        "in_scope": [
            "Player-language purity — no signals, methods, nodes, or class names",
            "Behavior completeness — are all player-visible behaviors described?",
            "Dependency symmetry — if System A lists System B as input, does B list A as output?",
            "Authority alignment — does data ownership match the authority table?",
        ],
        "out_of_scope": [
            "Code patterns or engine APIs",
            "Implementation algorithms",
            "Exact numeric tuning values",
        ],
    },
    "reference": {
        "in_scope": [
            "Data accuracy vs source systems — do values match what system designs declare?",
            "Coverage — are there gaps where source docs have data but this table doesn't?",
            "Cross-reference consistency — do entries align across reference docs?",
        ],
        "out_of_scope": [
            "Game design philosophy",
            "Numeric tuning (match source docs, don't evaluate balance)",
        ],
    },
    "engine": {
        "in_scope": [
            "Specificity — are conventions concrete enough to follow unambiguously?",
            "Convention completeness — are common patterns covered?",
            "No design-layer content — engine docs describe HOW, never WHAT",
        ],
        "out_of_scope": [
            "Game design decisions",
            "System behavior descriptions",
        ],
    },
    "input": {
        "in_scope": [
            "Action map completeness — are all player actions defined?",
            "Binding coverage — are all actions bound for the target input method?",
            "Design doc alignment — do actions match the design doc's player verbs?",
        ],
        "out_of_scope": [
            "Implementation details or engine input systems",
            "Code patterns",
        ],
    },
    "roadmap": {
        "in_scope": [
            "Phase coverage — does the roadmap cover start to ship?",
            "ADR feedback currency — have filed ADRs been absorbed into scope?",
            "Vision alignment — do phases serve the design doc's pillars?",
        ],
        "out_of_scope": [
            "Implementation details",
            "Task-level work items",
        ],
    },
    "phase": {
        "in_scope": [
            "Entry/exit criteria — are they specific and testable?",
            "ADR absorption — have relevant ADRs been accounted for?",
            "Scope clarity — is it clear what's in and out of this phase?",
            "System alignment — do included systems make sense together?",
        ],
        "out_of_scope": [
            "Detailed system design (that's the spec's job)",
            "Implementation specifics",
        ],
    },
    "slice": {
        "in_scope": [
            "Vertical coverage — does the slice exercise multiple systems end-to-end?",
            "Interface exercise — does it test system integration points?",
            "Phase alignment — is the slice scoped within its parent phase?",
        ],
        "out_of_scope": [
            "Implementation details",
            "Single-system depth (that's the spec's job)",
        ],
    },
    "spec": {
        "in_scope": [
            "Behavioral purity — describes WHAT, not HOW (no engine constructs)",
            "Acceptance criteria — are behaviors testable?",
            "System alignment — does the spec match its parent system design?",
            "State alignment — are state transitions consistent with state-transitions.md?",
        ],
        "out_of_scope": [
            "Engine constructs, code patterns, or node types",
            "Implementation algorithms",
        ],
    },
    "task": {
        "in_scope": [
            "Spec coverage — does the task implement all acceptance criteria from its spec?",
            "Step concreteness — are implementation steps specific enough to execute?",
            "File path validity — do referenced files match engine conventions?",
        ],
        "out_of_scope": [
            "Game design decisions or behavioral changes",
            "Spec-level scope changes",
        ],
    },
}

DOC_TYPE_CRITERIA = {
    "design": [
        "Vision clarity — is the core vision specific enough to guide downstream documents?",
        "Pillar consistency — do all sections reflect and serve the stated design pillars?",
        "Core loop definition — is the moment-to-moment player experience clear?",
        "System completeness — are all systems needed for a functional game identified?",
        "System index sync — does the System Design Index match registered system files?",
        "Scope boundaries — is it clear what the game IS and IS NOT?",
    ],
    "style": [
        "Design doc alignment — does visual identity serve the game's vision and pillars?",
        "Internal consistency — do style rules agree with color system and UI kit?",
        "Glossary compliance — are canonical terms used correctly (no synonyms from the NOT column)?",
        "Completeness — are all visual dimensions addressed (color, typography, spacing, animation)?",
    ],
    "system": [
        "Player-language purity — no signals, methods, nodes, or class names anywhere in the doc",
        "Behavior completeness — every player-visible action and its outcome is described",
        "Input/output symmetry — dependencies match between connected systems",
        "Authority alignment — data ownership matches scaffold/design/authority.md",
        "State coverage — all system states and transitions are defined",
    ],
    "reference": [
        "Source accuracy — data matches what system designs and authority table declare",
        "Coverage completeness — no gaps where source docs define data but this table is missing it",
        "Cross-reference consistency — entries align across all reference documents",
        "Format utility — structure is practical for downstream spec and task authors",
    ],
    "engine": [
        "Specificity — conventions are concrete enough to follow without interpretation",
        "Completeness — common development patterns are covered",
        "Layer purity — no game design content (engine docs are HOW, not WHAT)",
        "Internal consistency — rules don't contradict each other",
    ],
    "input": [
        "Action completeness — every player verb from the design doc has a corresponding action",
        "Binding coverage — all actions are bound for each input method",
        "Conflict freedom — no binding collisions within the same context",
        "Design doc alignment — action names use canonical glossary terms",
    ],
    "roadmap": [
        "Phase coverage — roadmap covers the full arc from first prototype to ship",
        "ADR currency — all filed ADRs have been evaluated and absorbed or deferred",
        "Vision alignment — phase goals serve the design doc's pillars and scope",
        "Dependency ordering — phases build on each other logically",
    ],
    "phase": [
        "Entry/exit criteria — specific, testable, and measurable",
        "ADR absorption — all relevant ADRs accounted for in scope adjustments",
        "System grouping — included systems logically belong together",
        "Scope boundaries — clear what is in and out of this phase",
    ],
    "slice": [
        "Vertical coverage — slice exercises multiple systems end-to-end",
        "Interface exercise — integration points between systems are tested",
        "Phase alignment — slice is properly scoped within its parent phase",
        "Spec decomposition — the slice breaks down into clear, atomic specs",
    ],
    "spec": [
        "Behavioral purity — WHAT not HOW; no engine constructs, node types, or code patterns",
        "Acceptance criteria — every behavior is testable and verifiable",
        "System alignment — spec matches the parent system design's declared behavior",
        "State consistency — state transitions match scaffold/design/state-transitions.md",
        "ADR awareness — relevant ADRs have been checked and absorbed",
    ],
    "task": [
        "Spec coverage — all acceptance criteria from the parent spec are addressed",
        "Step concreteness — each step is specific enough for a developer to execute",
        "File paths — referenced files match engine conventions and project structure",
        "Engine compliance — implementation follows engine doc constraints",
    ],
}


# ---------------------------------------------------------------------------
# Per-Provider Config Helpers
# ---------------------------------------------------------------------------

def get_max_tokens(config, provider):
    """Get max_tokens for a provider, falling back to global config."""
    provider_config = config.get(provider, {})
    return provider_config.get("max_tokens", config.get("max_tokens", 16384))


# ---------------------------------------------------------------------------
# API Calls — OpenAI
# ---------------------------------------------------------------------------

def call_openai(api_key, config, messages):
    """Call OpenAI API with JSON response format. Used for review and consensus."""
    import urllib.request
    import urllib.error

    provider_config = config.get("openai", {})
    model = provider_config.get("model", "gpt-4o")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": config.get("temperature", 0.3),
        "max_completion_tokens": get_max_tokens(config, "openai"),
        "response_format": {"type": "json_object"},
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
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
    import urllib.request
    import urllib.error

    provider_config = config.get("openai", {})
    model = provider_config.get("model", "gpt-4o")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": config.get("temperature", 0.3),
        "max_completion_tokens": get_max_tokens(config, "openai"),
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
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
    import urllib.request
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
        "max_tokens": get_max_tokens(config, "anthropic"),
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

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
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
    import urllib.request
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
        "max_tokens": get_max_tokens(config, "anthropic"),
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

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
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


# ---------------------------------------------------------------------------
# API Calls — Google (Gemini)
# ---------------------------------------------------------------------------

def call_google(api_key, config, messages):
    """Call Google Gemini API with JSON response. Used for review and consensus."""
    import urllib.request
    import urllib.error

    provider_config = config.get("google", {})
    model = provider_config.get("model", "gemini-2.5-pro")

    # Convert OpenAI-style messages to Gemini format
    system_text = ""
    gemini_contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        elif msg["role"] == "user":
            gemini_contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            gemini_contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": config.get("temperature", 0.3),
            "maxOutputTokens": get_max_tokens(config, "google"),
            "responseMimeType": "application/json",
        },
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"Google API error ({e.code}): {msg}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}


def call_google_raw(api_key, config, messages):
    """Call Google Gemini API returning raw text. Used for inner loop exchanges."""
    import urllib.request
    import urllib.error

    provider_config = config.get("google", {})
    model = provider_config.get("model", "gemini-2.5-pro")

    system_text = ""
    gemini_contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        elif msg["role"] == "user":
            gemini_contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            gemini_contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": config.get("temperature", 0.3),
            "maxOutputTokens": get_max_tokens(config, "google"),
        },
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": content}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        return {"error": f"Google API error ({e.code}): {msg}"}
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
# Billing / Quota Error Detection
# ---------------------------------------------------------------------------

BILLING_ERROR_PATTERNS = [
    "insufficient_quota", "billing", "insufficient_funds", "payment",
    "exceeded your current quota", "account is not active",
    "rate_limit", "too many requests", "overloaded",
]


def is_billing_error(result):
    """Check if an API error result indicates a billing/quota/rate issue."""
    if "error" not in result:
        return False
    error_msg = result["error"].lower()
    # HTTP 402 (Payment Required), 429 (Rate Limit), 529 (Overloaded)
    for code in ["(402)", "(429)", "(529)"]:
        if code in error_msg:
            return True
    for pattern in BILLING_ERROR_PATTERNS:
        if pattern in error_msg:
            return True
    return False


# ---------------------------------------------------------------------------
# Provider Dispatch
# ---------------------------------------------------------------------------

def _call_single_provider(provider, api_key, config, messages, json_mode):
    """Call a single provider. Returns (result, provider_name)."""
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
    elif provider == "google":
        if json_mode:
            return call_google(api_key, config, messages)
        else:
            return call_google_raw(api_key, config, messages)
    else:
        return {"error": f"Unknown provider: {provider}. Use 'openai', 'anthropic', or 'google'."}


def _get_api_key_for_provider(config, provider):
    """Resolve API key for a specific provider (not necessarily the primary one)."""
    provider_config = config.get(provider, {})
    env_var = provider_config.get("api_key_env", f"{provider.upper()}_API_KEY")

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
    return key


def call_provider(api_key, config, messages, json_mode=True):
    """Route to the correct provider's API call, with fallback on billing errors."""
    fallback_order = config.get("fallback_order", [config.get("provider", "openai")])
    primary = config.get("provider", "openai")

    # Ensure primary is first in the fallback order
    if primary in fallback_order:
        fallback_order = [primary] + [p for p in fallback_order if p != primary]
    else:
        fallback_order = [primary] + fallback_order

    errors_encountered = []

    for provider in fallback_order:
        # Get API key for this provider
        if provider == primary:
            pkey = api_key
        else:
            pkey = _get_api_key_for_provider(config, provider)
            if not pkey:
                errors_encountered.append(f"{provider}: no API key configured")
                continue

        result = _call_single_provider(provider, pkey, config, messages, json_mode)

        if "error" not in result:
            # Success — annotate which provider was used if it wasn't the primary
            if provider != primary:
                result["_fallback_provider"] = provider
                print(f"[FALLBACK] Primary provider ({primary}) failed, using {provider}", file=sys.stderr)
            return result

        if is_billing_error(result):
            errors_encountered.append(f"{provider}: {result['error']}")
            print(f"[FALLBACK] {provider} billing/quota error, trying next provider...", file=sys.stderr)
            continue
        else:
            # Non-billing error (e.g., bad request, server error) — don't fallback, return immediately
            return result

    # All providers exhausted
    return {
        "error": "All providers exhausted — billing or quota errors on all configured providers",
        "providers_tried": errors_encountered,
        "fallback": "self-review",
    }


# ---------------------------------------------------------------------------
# Glossary Loader
# ---------------------------------------------------------------------------

def load_glossary():
    """Load glossary from the scaffold design directory."""
    glossary_path = Path(__file__).parent.parent / "design" / "glossary.md"
    if glossary_path.exists():
        return glossary_path.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

def build_system_prompt():
    """Build the reviewer persona prompt. Engine-agnostic."""
    return """You are a senior game developer and software architect acting as an adversarial
document reviewer for a game project that uses a structured document pipeline.

The project follows a strict document authority chain:
  Rank 1: Design doc (core vision)
  Rank 2: Style guide, color system, UI kit, glossary
  Rank 3: Input docs
  Rank 4: Interfaces, authority table
  Rank 5: System designs, state machines
  Rank 6: Reference tables
  Rank 7: Phase gates
  Rank 8: Behavior specs
  Rank 9: Implementation tasks
  Rank 10: Engine docs
  Rank 11: Theory docs (advisory only)

Design documents describe WHAT the game is (player-visible behavior only).
Engine documents describe HOW to build it (implementation patterns).
These layers must never be mixed.

You are in a multi-turn conversation with the document author (an AI assistant).
- In the first message, you receive the document and provide your review as structured JSON.
- In subsequent messages, the author responds to your issues — agreeing, partially agreeing,
  or pushing back with reasoning.
- Engage substantively: accept good reasoning, push back on weak reasoning,
  acknowledge when the author makes a valid point.
- When asked for consensus, output a final JSON summary.

Always respond with valid JSON when starting a review or providing a final summary.
In discussion exchanges, you may use natural language with embedded JSON for clarity."""


def build_review_prompt(doc_content, doc_type, context="", focus="", glossary=""):
    """Build the initial review prompt with scope, criteria, and the document."""
    type_desc = DOC_TYPE_CONTEXT.get(doc_type, f"a {doc_type} document")
    scope = DOC_TYPE_SCOPE.get(doc_type, {"in_scope": [], "out_of_scope": []})
    criteria = DOC_TYPE_CRITERIA.get(doc_type, [])

    scope_text = "\n\nREVIEW SCOPE BOUNDARIES:"
    scope_text += "\nIN SCOPE (raise issues about these):"
    for item in scope["in_scope"]:
        scope_text += f"\n- {item}"
    scope_text += "\n\nOUT OF SCOPE (do NOT raise issues about these):"
    for item in scope["out_of_scope"]:
        scope_text += f"\n- {item}"

    criteria_text = "\n\nEvaluation criteria (specific to this document type):"
    for i, c in enumerate(criteria, 1):
        criteria_text += f"\n{i}. {c}"

    focus_text = ""
    if focus:
        focus_text = f"\n\nREVIEW FOCUS: Concentrate on: {focus}\nOnly flag issues outside the focus area if they are HIGH severity."

    glossary_text = ""
    if glossary:
        glossary_text = f"\n\nPROJECT GLOSSARY (flag any deviations from these canonical terms):\n{glossary}"

    return f"""Review this document. It is {type_desc}.
Pipeline: design doc -> style docs -> systems -> reference docs -> engine docs -> roadmap -> phases -> slices -> specs -> tasks.
{f"Additional context:{chr(10)}{context}" if context else ""}
{scope_text}
{criteria_text}
{focus_text}
{glossary_text}

Respond with a JSON object:
{{
    "summary": "1-2 sentence overall assessment",
    "issues": [
        {{
            "id": 1,
            "severity": "HIGH | MEDIUM | LOW",
            "location": "section name or quote",
            "problem": "what is wrong and why",
            "suggestion": "specific fix"
        }}
    ],
    "strengths": ["max 3"],
    "overall_quality": "POOR | FAIR | GOOD | EXCELLENT"
}}

Be specific. Every issue needs a concrete location and actionable suggestion.
Do NOT raise issues about OUT OF SCOPE items.
An empty issues array means you found nothing wrong.

Document:

---
{doc_content}
---"""


def build_consensus_request():
    """Prompt to ask reviewer for final consensus summary."""
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
        "specific change 1 to make to the document",
        "specific change 2 to make to the document"
    ],
    "remaining_disagreements": [],
    "overall_assessment": "updated assessment after discussion"
}

Set consensus_reached to true if all issues are either resolved or rejected with defensible reasoning.
Only set false if a HIGH severity issue remains with genuinely inadequate reasoning for rejection."""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_review(args):
    """Start a fresh review iteration. Creates conversation state."""
    config = load_config(getattr(args, 'profile', None))
    api_key = get_api_key(config)

    doc_path = Path(args.doc_path)
    if not doc_path.exists():
        print(json.dumps({"error": f"Document not found: {doc_path}"}))
        sys.exit(1)

    doc_content = doc_path.read_text(encoding="utf-8")

    # Detect or use provided doc type
    doc_type = args.type
    if not doc_type:
        doc_type = detect_doc_type(args.doc_path)
    if not doc_type:
        print(json.dumps({
            "error": "Could not detect document type from path",
            "fix": "Use --type to specify: design, style, system, reference, engine, input, roadmap, phase, slice, spec, task"
        }))
        sys.exit(1)

    # Load context files
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

    glossary = load_glossary()

    # Build messages
    system_msg = build_system_prompt()
    user_msg = build_review_prompt(
        doc_content, doc_type, context_str,
        focus=args.focus or "", glossary=glossary
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    result = call_provider(api_key, config, messages, json_mode=True)

    if "error" in result:
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Get tier info
    tier_name, tier_config = get_tier(doc_type)

    # Save conversation state
    messages.append({"role": "assistant", "content": json.dumps(result)})

    conv_state = {
        "document": str(doc_path),
        "type": doc_type,
        "tier": tier_name,
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

    state_path = conv_path(args.doc_path, args.iteration)
    save_conversation(state_path, conv_state)

    # Add meta to output
    result["_meta"] = {
        "document": str(doc_path),
        "type": doc_type,
        "tier": tier_name,
        "tier_max_iterations": tier_config["max_iterations"],
        "tier_max_exchanges": tier_config["max_exchanges"],
        "tier_severity_filter": tier_config["severity_filter"],
        "iteration": args.iteration,
        "exchange": 1,
        "provider": config.get("provider", "openai"),
        "model": conv_state["model"],
        "conversation_file": str(state_path),
        "issue_count": len(result.get("issues", [])),
    }

    print(json.dumps(result, indent=2))


def cmd_respond(args):
    """Continue the conversation within an iteration."""
    config = load_config(getattr(args, 'profile', None))
    api_key = get_api_key(config)

    state_path = conv_path(args.doc_path, args.iteration)
    conv_state = load_conversation(state_path)

    if not conv_state:
        print(json.dumps({
            "error": f"No conversation found for iteration {args.iteration}",
            "fix": f"Run 'review' first: python doc-review.py review {args.doc_path} --iteration {args.iteration}"
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

    # Call provider with full conversation history (raw text mode)
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
            "document": conv_state["document"],
            "iteration": conv_state["iteration"],
            "exchange": conv_state["exchange"],
            "total_messages": len(conv_state["messages"]),
            "conversation_file": str(state_path),
        }
    }

    print(json.dumps(output, indent=2))


def cmd_consensus(args):
    """Ask reviewer for final consensus summary after discussion."""
    config = load_config(getattr(args, 'profile', None))
    api_key = get_api_key(config)

    state_path = conv_path(args.doc_path, args.iteration)
    conv_state = load_conversation(state_path)

    if not conv_state:
        print(json.dumps({"error": f"No conversation found for iteration {args.iteration}"}))
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
        "document": conv_state["document"],
        "iteration": conv_state["iteration"],
        "exchanges": conv_state["exchange"],
        "conversation_file": str(state_path),
    }

    print(json.dumps(result, indent=2))


def cmd_check_config(args):
    """Verify configuration, API key, and glossary availability."""
    config = load_config(getattr(args, 'profile', None))
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

    glossary = load_glossary()

    # List supported doc types and their tiers
    type_tiers = {}
    for tier_name, tier_cfg in TIERS.items():
        for t in tier_cfg["types"]:
            type_tiers[t] = tier_name

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
        "glossary_found": bool(glossary),
        "glossary_lines": len(glossary.splitlines()) if glossary else 0,
        "doc_types": list(type_tiers.keys()),
        "tiers": {name: {
            "max_iterations": cfg["max_iterations"],
            "max_exchanges": cfg["max_exchanges"],
            "severity_filter": cfg["severity_filter"],
            "types": cfg["types"],
        } for name, cfg in TIERS.items()},
    }

    if not has_key:
        result["warning"] = f"API key not found. Set {env_var} in your environment or create scaffold/.env with:\n{env_var}=your-key-here"

    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Adversarial document reviewer — multi-provider (OpenAI / Anthropic / Google)"
    )
    parser.add_argument("--profile", default=None, help="Config profile to use (e.g., 'code_review'). Overrides provider/model from review_config.json.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # review — start fresh iteration
    p_review = subparsers.add_parser("review", help="Start a fresh review (new iteration)")
    p_review.add_argument("doc_path", help="Path to document to review")
    p_review.add_argument(
        "--type",
        choices=["design", "style", "system", "reference", "engine", "input",
                 "roadmap", "phase", "slice", "spec", "task"],
        default=None,
        help="Document type (auto-detected from path if omitted)"
    )
    p_review.add_argument("--iteration", type=int, default=1, help="Outer loop iteration number")
    p_review.add_argument("--context-files", nargs="*", default=[], help="Supporting document paths")
    p_review.add_argument("--focus", default="", help="Review focus area")

    # respond — continue conversation within an iteration
    p_respond = subparsers.add_parser("respond", help="Continue conversation (send Claude's response)")
    p_respond.add_argument("doc_path", help="Path to document being reviewed")
    p_respond.add_argument("--iteration", type=int, required=True, help="Which iteration to continue")
    p_respond.add_argument("--message", default="", help="Claude's response text")
    p_respond.add_argument("--message-file", default="", help="File containing Claude's response")

    # consensus — request final consensus summary
    p_consensus = subparsers.add_parser("consensus", help="Request consensus summary for iteration")
    p_consensus.add_argument("doc_path", help="Path to document being reviewed")
    p_consensus.add_argument("--iteration", type=int, required=True, help="Which iteration")

    # check-config
    subparsers.add_parser("check-config", help="Verify configuration and API key")

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
