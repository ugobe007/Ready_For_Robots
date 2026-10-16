"""
Taxonomy-based semantic extraction for robot classification.

Uses LLM with structured output (enum schema) to extract classification
values that conform exactly to taxonomy.v1.json. Evidence is validated
against page text.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from anthropic import Anthropic


TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "tests/fixtures/taxonomy.v1.json"
CONFIG_PATH = Path(__file__).resolve().parent / "extraction_config.json"
PROMPT_VERSION = "v6"

SINGLE_VALUE_FIELDS = ("offering_type", "form", "primary_class", "primary_function")
LIST_FIELDS = ("secondary_functions", "industries")

_EVIDENCE_CHARS = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"', "\u2033": '"',
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-", "\u2212": "-",
})
_ELLIPSIS = re.compile(r"\.{3,}|\u2026")


def load_taxonomy() -> dict[str, Any]:
    """Load taxonomy (single source of truth)."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def load_extraction_config() -> dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def taxonomy_values(taxonomy: dict[str, Any], section: str) -> list[str]:
    """Closed values for a section; keys starting with '_' are documentation."""
    return [k for k in taxonomy[section] if not k.startswith("_")]


def industry_prompt_lines(taxonomy: dict[str, Any]) -> list[str]:
    industries = taxonomy["industries"]
    return [f"- {key}: {industries[key]}" for key in taxonomy_values(taxonomy, "industries")]


def get_taxonomy_version() -> str:
    """Get taxonomy version for cache keying."""
    taxonomy = load_taxonomy()
    return taxonomy.get("version", "v1")


def build_extraction_schema(taxonomy: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build JSON schema with enums loaded from taxonomy.
    
    This enforces that the model can only return values from the closed lists.
    """
    # Extract enum values from taxonomy
    offering_types = taxonomy_values(taxonomy, "offering_type")
    functions = taxonomy_values(taxonomy, "functions")
    industries = taxonomy_values(taxonomy, "industries")
    forms = taxonomy_values(taxonomy, "form")
    primary_classes = taxonomy_values(taxonomy, "primary_class")
    config = config or load_extraction_config()
    
    schema = {
        "type": "object",
        "properties": {
            "page_type": {
                "type": "object",
                "description": "Step 1: what kind of page this is, decided before any product record",
                "properties": {
                    "value": {"type": "string", "enum": list(config["page_types"])},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {
                        "type": "string",
                        "description": "One contiguous quote copied exactly from the page",
                    },
                },
                "required": ["value", "confidence", "evidence"],
            },
            "products": {
                "type": "array",
                "description": "Robot products on this page, one record per product. Empty unless page_type is manufacturer_product_page.",
                "maxItems": config["max_records_per_page"],
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company name"
                        },
                        "product_name": {
                            "type": "string",
                            "description": "Product name"
                        },
                        "offering_type": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "enum": offering_types,
                                    "description": "Type of offering"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Confidence score (0-1)"
                                },
                                "evidence": {
                                    "type": "string",
                                    "description": "Exact quote from page supporting this classification"
                                }
                            },
                            "required": ["value", "confidence", "evidence"]
                        },
                        "form": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "enum": forms,
                                    "description": "Physical form of the robot"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "evidence": {
                                    "type": "string",
                                    "description": "Exact quote from page"
                                }
                            },
                            "required": ["value", "confidence", "evidence"]
                        },
                        "primary_class": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "enum": primary_classes,
                                    "description": "Primary classification (index shelf)"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "evidence": {
                                    "type": "string",
                                    "description": "Exact quote from page"
                                }
                            },
                            "required": ["value", "confidence", "evidence"]
                        },
                        "primary_function": {
                            "type": "object",
                            "description": "The ONE primary function this robot is designed for",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "enum": functions,
                                    "description": "Primary function from taxonomy"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "evidence": {
                                    "type": "string",
                                    "description": "Exact quote from page"
                                }
                            },
                            "required": ["value", "confidence", "evidence"]
                        },
                        "secondary_functions": {
                            "type": "array",
                            "description": "0-2 secondary functions. Leave empty if robot is single-purpose.",
                            "maxItems": 2,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "enum": functions,
                                        "description": "Secondary function from taxonomy"
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1
                                    },
                                    "evidence": {
                                        "type": "string",
                                        "description": "Exact quote from page"
                                    }
                                },
                                "required": ["value", "confidence", "evidence"]
                            }
                        },
                        "industries": {
                            "type": "array",
                            "description": "Industries where this robot is sold",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "enum": industries,
                                        "description": "Industry from taxonomy"
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1
                                    },
                                    "evidence": {
                                        "type": "string",
                                        "description": "Exact quote from page"
                                    }
                                },
                                "required": ["value", "confidence", "evidence"]
                            }
                        },
                        "unclassified_notes": {
                            "type": "string",
                            "description": "Any information that didn't fit the taxonomy; logged for review"
                        }
                    },
                    "required": [
                        "company",
                        "product_name",
                        "offering_type",
                        "form",
                        "primary_class",
                        "primary_function",
                        "industries"
                    ]
                }
            }
        },
        "required": ["page_type", "products"]
    }
    
    return schema


def normalize_for_evidence(text: str) -> str:
    """Whitespace, curly/straight quotes, dashes, and case."""
    return " ".join(text.translate(_EVIDENCE_CHARS).split()).lower()


def validate_evidence(evidence: str, page_text: str) -> bool:
    """
    Evidence is split on "..." and every piece must appear on the page, in order.

    Both sides are normalized first (see normalize_for_evidence).
    """
    if not evidence or not page_text:
        return False
    page = normalize_for_evidence(page_text)
    pieces = [p.strip() for p in _ELLIPSIS.split(normalize_for_evidence(evidence))]
    pieces = [p for p in pieces if p]
    if not pieces:
        return False
    pos = 0
    for piece in pieces:
        found = page.find(piece, pos)
        if found < 0:
            return False
        pos = found + len(piece)
    return True


def _fact_text(fact: Any) -> str | None:
    if isinstance(fact, dict):
        value = fact.get("value")
        text = str(value).strip() if value not in (None, "") else ""
        return text or None
    if isinstance(fact, str) and fact.strip():
        return fact.strip()
    return None


def _assign_product_class(product: dict[str, Any]) -> dict[str, Any]:
    """Replace the model's class with the rule-table class. The guess is kept aside."""
    from app.services.robot_understanding_v1.class_rules import assign_class

    prior = product.get("model_class_suggestion")
    suggestion = prior.strip() if isinstance(prior, str) and prior.strip() else _fact_text(product.get("primary_class"))
    industries = [value for item in (product.get("industries") or []) if (value := _fact_text(item))]
    assigned, rule_id, reason = assign_class(
        _fact_text(product.get("primary_function")),
        industries,
        _fact_text(product.get("form")),
    )
    product["model_class_suggestion"] = suggestion
    product["class_rule_id"] = rule_id
    product["class_rule_reason"] = reason
    product["needs_review"] = assigned is None
    if assigned is None:
        product["primary_class"] = None
    else:
        product["primary_class"] = {
            "value": assigned,
            "rule_id": rule_id,
            "reason": reason,
            "assigned_by": "class_rules",
        }
    return product


def apply_evidence_policy(
    product: dict[str, Any],
    page_text: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove facts whose evidence is not a normalized substring of the page.

    Removed facts are moved to `unsupported_facts` with confidence capped, so
    they stay visible in logs but nothing downstream (scoring, matching) can
    read them from the product record. An unsupported single-value field is
    set to None.
    """
    cap = config["unsupported_confidence_cap"]
    exclude = config["exclude_unsupported_facts"]
    out = dict(product)
    unsupported = []

    def supported(fact: Any) -> bool:
        return isinstance(fact, dict) and validate_evidence(fact.get("evidence", ""), page_text)

    def log(field: str, fact: Any) -> None:
        entry = dict(fact) if isinstance(fact, dict) else {"value": fact}
        entry["field"] = field
        entry["confidence"] = min(float(entry.get("confidence") or 0), cap)
        unsupported.append(entry)

    for field in SINGLE_VALUE_FIELDS:
        fact = product.get(field)
        if fact is None:
            continue
        if supported(fact):
            out[field] = {**fact, "evidence_validated": True}
        else:
            log(field, fact)
            out[field] = None if exclude else {**fact, "confidence": min(fact.get("confidence", 0), cap), "evidence_validated": False}

    for field in LIST_FIELDS:
        kept = []
        for fact in product.get(field) or []:
            if supported(fact):
                kept.append({**fact, "evidence_validated": True})
            else:
                log(field, fact)
                if not exclude and isinstance(fact, dict):
                    kept.append({**fact, "confidence": min(fact.get("confidence", 0), cap), "evidence_validated": False})
        out[field] = kept

    out["unsupported_facts"] = unsupported
    return out


def _coerce_products(raw: Any) -> list[dict[str, Any]]:
    """The model occasionally returns the products list, or an item, as a JSON string."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"products is an unparseable string: {raw[:120]!r}")
    if isinstance(raw, dict):
        raw = [raw]
    products = []
    for item in raw or []:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except json.JSONDecodeError:
                raise ValueError(f"product is an unparseable string: {item[:120]!r}")
        if not isinstance(item, dict):
            raise ValueError(f"product has unexpected type {type(item).__name__}")
        products.append(item)
    return products


def _call_with_retry(client: Any, request: dict[str, Any], retries: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retry only when the response has no usable structure; never on content.

    Tokens from every attempt are counted.
    """
    call = {"input_tokens": 0, "output_tokens": 0, "attempts": 0, "errors": [], "model": None}
    for _ in range(retries + 1):
        response = client.messages.create(**request)
        call["attempts"] += 1
        call["input_tokens"] += response.usage.input_tokens
        call["output_tokens"] += response.usage.output_tokens
        call["model"] = response.model
        tool_result = next(
            (b.input for b in response.content if b.type == "tool_use" and b.name == "classify_robot"),
            None,
        )
        try:
            if not tool_result:
                raise ValueError(f"No tool call returned from LLM (stop_reason={response.stop_reason})")
            return {**tool_result, "products": _coerce_products(tool_result.get("products", []))}, call
        except ValueError as e:
            call["errors"].append(str(e)[:200])
    raise ValueError(f"Malformed output after {call['attempts']} attempts: {call['errors'][-1]}")


def _matches_hint(product: dict[str, Any], hint: str) -> bool:
    name = (product.get("product_name") or "").lower()
    hint = hint.lower()
    return bool(name) and (hint in name or name in hint)


def cap_records(products: list[dict[str, Any]], hint: str | None, cap: int) -> list[dict[str, Any]]:
    """The hinted product (if any) plus the first others, at most `cap` in total."""
    if hint:
        target = [p for p in products if _matches_hint(p, hint)][:1]
        products = target + [p for p in products if p not in target]
    return products[:cap]


def page_record(raw_page_type: Any, page_text: str, config: dict[str, Any]) -> dict[str, Any]:
    """Page-level classification. Evidence is checked and logged but never blanks the page type."""
    fact = raw_page_type if isinstance(raw_page_type, dict) else {"value": raw_page_type}
    value = fact.get("value")
    produces_records = value in config["record_page_types"]
    record = {
        "page_type": value,
        "confidence": fact.get("confidence"),
        "evidence": fact.get("evidence", ""),
        "evidence_validated": validate_evidence(fact.get("evidence", ""), page_text),
        "produces_records": produces_records,
    }
    if not produces_records:
        record["offering_type"] = "non_robot"
    return record


def extract_robot_taxonomy(
    url: str,
    page_text: str,
    product_name_hint: str | None = None,
    cache_key_extra: str = "v1"
) -> dict[str, Any]:
    """
    Extract robot classification using LLM with taxonomy-enforced schema.
    
    Args:
        url: Robot company URL
        page_text: Page text content
        product_name_hint: Optional product name to focus extraction
        cache_key_extra: Extra cache key component (for prompt versioning)
    
    Returns:
        {
            "products": [
                {
                    "company": str,
                    "product_name": str,
                    "offering_type": {"value": str, "confidence": float, "evidence": str},
                    "form": {...},
                    "primary_class": {...},
                    "primary_function": {"value": str, "confidence": float, "evidence": str},
                    "secondary_functions": [{"value": str, "confidence": float, "evidence": str}],  # 0-2
                    "industries": [...],
                    "unclassified_notes": str
                }
            ],
            "extraction_metadata": {
                "taxonomy_version": str,
                "cache_key": str,
                "tokens_used": int,
                "model": str,
                "prompt_version": str
            }
        }
    """
    taxonomy = load_taxonomy()
    config = load_extraction_config()
    schema = build_extraction_schema(taxonomy, config)
    cap = config["max_records_per_page"]
    
    # Build cache key
    page_hash = hashlib.sha256(page_text.encode()).hexdigest()[:16]
    taxonomy_version = get_taxonomy_version()
    prompt_version = PROMPT_VERSION
    hint_suffix = f":{product_name_hint}" if product_name_hint else ""
    cache_key = f"{url}:{page_hash}:{taxonomy_version}:{prompt_version}:{cache_key_extra}{hint_suffix}"
    
    # Build prompt
    prompt_parts = [
        "Extract robot product classification from this page.",
        "",
        "STEP 1 - PAGE TYPE. Classify the page itself before anything else:",
        *[f"- {name}: {meaning}" for name, meaning in config["page_types"].items()],
        f"Only {' or '.join(config['record_page_types'])} produces product records.",
        "For any other page type, return page_type and an EMPTY products list.",
        "",
        "STEP 2 - PRODUCT RECORDS (manufacturer pages only).",
        "",
        "CRITICAL RULES:",
        "1. Use ONLY values from the provided taxonomy. Never invent categories.",
        f"2. One record per robot product, at most {cap} records in total"
        + (f": the FOCUS product plus at most {cap - 1} others." if product_name_hint
           else ": the most prominent robot products on the page."),
        "3. Every evidence value is ONE contiguous passage copied exactly from the page text,",
        "   character for character. Do not join separate passages, do not use '...',",
        "   do not join a heading to the text under it, do not add, drop, or reword anything.",
        "4. Set confidence based on evidence clarity (0.0-1.0).",
        "5. If information doesn't fit the taxonomy, note it in unclassified_notes.",
        "",
    ]
    
    if product_name_hint:
        prompt_parts.extend([
            f"FOCUS: Extract information specifically about the product '{product_name_hint}'.",
            "Other products on the page are secondary.",
            "",
        ])
    
    prompt_parts.extend([
        "TAXONOMY:",
        "",
        f"offering_type: {', '.join(taxonomy_values(taxonomy, 'offering_type'))}",
        f"functions: {', '.join(taxonomy_values(taxonomy, 'functions'))}",
        f"form: {', '.join(taxonomy_values(taxonomy, 'form'))}",
        f"primary_class: {', '.join(taxonomy_values(taxonomy, 'primary_class'))}",
        "",
        "INDUSTRY DEFINITION:",
        taxonomy["industries"]["_definition"],
        "",
        "industries (value: what it covers):",
        *industry_prompt_lines(taxonomy),
        "",
        "INDUSTRY EVIDENCE REQUIREMENT:",
        "Only output an industry if the page explicitly NAMES:",
        "- That market (e.g., 'for hospitals', 'in warehouses')",
        "- A customer in it (e.g., 'FedEx uses this robot')",
        "- A deployment there (e.g., 'deployed at manufacturing sites')",
        "",
        "Do NOT infer industries from robot capabilities alone.",
        "Vision equipment ≠ inspection robot. Material handling ≠ delivery service.",
        "",
        "PRIMARY FUNCTION:",
        "Choose exactly ONE primary function - the robot's main purpose.",
        "Only add secondary functions (0-2) if the page explicitly describes",
        "additional capabilities the robot is designed for.",
        "",
        "PAGE TEXT:",
        "",
        page_text,
    ])
    
    prompt = "\n".join(prompt_parts)
    
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    request = dict(
        model="claude-sonnet-4-6",
        max_tokens=config["max_output_tokens"],
        # SDK 1.x dropped the typed temperature keyword. claude-sonnet-4-6 still
        # accepts the field, so it goes out in the body from the config value.
        extra_body={"temperature": config["temperature"]},
        system=[
            {
                "type": "text",
                "text": "You are a robot classification expert. Extract structured data using only the provided taxonomy values.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": prompt}],
        tools=[
            {
                "name": "classify_robot",
                "description": "Classify robot products using taxonomy values",
                "input_schema": schema
            }
        ],
        tool_choice={"type": "tool", "name": "classify_robot"},
    )
    tool_result, call = _call_with_retry(client, request, config.get("max_malformed_output_retries", 0))

    page = page_record(tool_result.get("page_type"), page_text, config)
    raw_products = tool_result["products"] if page["produces_records"] else []
    kept = cap_records(raw_products, product_name_hint, cap)
    for product in kept:
        if isinstance(product, dict):
            product["model_class_suggestion"] = _fact_text(product.get("primary_class"))
    validated_products = [_assign_product_class(apply_evidence_policy(product, page_text, config)) for product in kept]

    return {
        "page": page,
        "products": validated_products,
        "extraction_metadata": {
            "taxonomy_version": taxonomy_version,
            "prompt_version": prompt_version,
            "cache_key": cache_key,
            "tokens_used": call["input_tokens"] + call["output_tokens"],
            "input_tokens": call["input_tokens"],
            "output_tokens": call["output_tokens"],
            "model": call["model"],
            "attempts": call["attempts"],
            "malformed_attempt_errors": call["errors"],
            "records_returned": len(raw_products),
            "records_dropped_by_page_type": 0 if page["produces_records"] else len(tool_result["products"]),
            "records_dropped_by_cap": len(raw_products) - len(kept),
            "extraction_config": config,
        }
    }
