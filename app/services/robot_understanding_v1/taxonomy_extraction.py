"""
Taxonomy-based semantic extraction for robot classification.

Uses LLM with structured output (enum schema) to extract classification
values that conform exactly to taxonomy.v1.json. Evidence is validated
against page text.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic


TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "tests/fixtures/taxonomy.v1.json"
CONFIG_PATH = Path(__file__).resolve().parent / "extraction_config.json"
PROMPT_VERSION = "v3"

SINGLE_VALUE_FIELDS = ("offering_type", "form", "primary_class", "primary_function")
LIST_FIELDS = ("secondary_functions", "industries")


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


def get_taxonomy_version() -> str:
    """Get taxonomy version for cache keying."""
    taxonomy = load_taxonomy()
    return taxonomy.get("version", "v1")


def build_extraction_schema(taxonomy: dict[str, Any]) -> dict[str, Any]:
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
    
    schema = {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "description": "List of robot products found on this page. One record per product.",
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
        "required": ["products"]
    }
    
    return schema


def validate_evidence(evidence: str, page_text: str) -> bool:
    """
    Check if evidence snippet is an exact substring of page text.
    
    Case-insensitive and whitespace-normalized comparison.
    """
    if not evidence or not page_text:
        return False
    
    # Normalize whitespace
    evidence_norm = " ".join(evidence.split()).lower()
    page_norm = " ".join(page_text.split()).lower()
    
    return evidence_norm in page_norm


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
    schema = build_extraction_schema(taxonomy)
    
    # Build cache key
    page_hash = hashlib.sha256(page_text.encode()).hexdigest()[:16]
    taxonomy_version = get_taxonomy_version()
    prompt_version = PROMPT_VERSION
    hint_suffix = f":{product_name_hint}" if product_name_hint else ""
    cache_key = f"{url}:{page_hash}:{taxonomy_version}:{prompt_version}:{cache_key_extra}{hint_suffix}"
    
    # Build prompt
    prompt_parts = [
        "Extract robot product classification from this company page.",
        "",
        "CRITICAL RULES:",
        "1. Use ONLY values from the provided taxonomy. Never invent categories.",
        "2. Extract one record per robot product. Multi-product sites get multiple records.",
        "3. Every field must have an evidence snippet that is an EXACT QUOTE from the page.",
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
        f"industries: {', '.join(taxonomy_values(taxonomy, 'industries'))}",
        f"form: {', '.join(taxonomy_values(taxonomy, 'form'))}",
        f"primary_class: {', '.join(taxonomy_values(taxonomy, 'primary_class'))}",
        "",
        "INDUSTRY DEFINITION:",
        taxonomy["industries"]["_definition"],
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
    
    # Call LLM with structured output
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "You are a robot classification expert. Extract structured data using only the provided taxonomy values.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        tools=[
            {
                "name": "classify_robot",
                "description": "Classify robot products using taxonomy values",
                "input_schema": schema
            }
        ],
        tool_choice={"type": "tool", "name": "classify_robot"}
    )
    
    # Extract tool call result
    tool_result = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_robot":
            tool_result = block.input
            break
    
    if not tool_result:
        raise ValueError(f"No tool call returned from LLM (stop_reason={response.stop_reason})")
    
    config = load_extraction_config()
    validated_products = [
        apply_evidence_policy(product, page_text, config)
        for product in _coerce_products(tool_result.get("products", []))
    ]
    
    return {
        "products": validated_products,
        "extraction_metadata": {
            "taxonomy_version": taxonomy_version,
            "prompt_version": prompt_version,
            "cache_key": cache_key,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": response.model,
            "extraction_config": config,
        }
    }
