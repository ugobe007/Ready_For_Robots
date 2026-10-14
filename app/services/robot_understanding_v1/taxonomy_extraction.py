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


def load_taxonomy() -> dict[str, Any]:
    """Load taxonomy (single source of truth)."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


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
    offering_types = list(taxonomy["offering_type"].keys())
    functions = list(taxonomy["functions"].keys())
    industries = list(taxonomy["industries"].keys())
    forms = list(taxonomy["form"].keys())
    primary_classes = list(taxonomy["primary_class"].keys())
    
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
                        "functions": {
                            "type": "array",
                            "description": "1-3 functions the robot is designed for",
                            "minItems": 1,
                            "maxItems": 3,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "enum": functions,
                                        "description": "Function from taxonomy"
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
                        "functions",
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


def validate_and_cap_confidence(
    product: dict[str, Any],
    page_text: str
) -> dict[str, Any]:
    """
    Validate evidence snippets and cap confidence at 0.3 for unsupported facts.
    
    This prevents the model from inventing industries for vague pages.
    """
    validated = product.copy()
    
    # Check offering_type
    if not validate_evidence(product["offering_type"]["evidence"], page_text):
        validated["offering_type"]["confidence"] = min(
            validated["offering_type"]["confidence"],
            0.3
        )
        validated["offering_type"]["evidence_validated"] = False
    else:
        validated["offering_type"]["evidence_validated"] = True
    
    # Check form
    if not validate_evidence(product["form"]["evidence"], page_text):
        validated["form"]["confidence"] = min(validated["form"]["confidence"], 0.3)
        validated["form"]["evidence_validated"] = False
    else:
        validated["form"]["evidence_validated"] = True
    
    # Check primary_class
    if not validate_evidence(product["primary_class"]["evidence"], page_text):
        validated["primary_class"]["confidence"] = min(
            validated["primary_class"]["confidence"],
            0.3
        )
        validated["primary_class"]["evidence_validated"] = False
    else:
        validated["primary_class"]["evidence_validated"] = True
    
    # Check functions
    validated["functions"] = []
    for func in product.get("functions", []):
        validated_func = func.copy()
        if not validate_evidence(func["evidence"], page_text):
            validated_func["confidence"] = min(validated_func["confidence"], 0.3)
            validated_func["evidence_validated"] = False
        else:
            validated_func["evidence_validated"] = True
        validated["functions"].append(validated_func)
    
    # Check industries
    validated["industries"] = []
    for ind in product.get("industries", []):
        validated_ind = ind.copy()
        if not validate_evidence(ind["evidence"], page_text):
            validated_ind["confidence"] = min(validated_ind["confidence"], 0.3)
            validated_ind["evidence_validated"] = False
        else:
            validated_ind["evidence_validated"] = True
        validated["industries"].append(validated_ind)
    
    return validated


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
                    "functions": [{"value": str, "confidence": float, "evidence": str}],
                    "industries": [...],
                    "unclassified_notes": str
                }
            ],
            "extraction_metadata": {
                "taxonomy_version": str,
                "cache_key": str,
                "tokens_used": int,
                "model": str
            }
        }
    """
    taxonomy = load_taxonomy()
    schema = build_extraction_schema(taxonomy)
    
    # Build cache key
    page_hash = hashlib.sha256(page_text.encode()).hexdigest()[:16]
    taxonomy_version = get_taxonomy_version()
    hint_suffix = f":{product_name_hint}" if product_name_hint else ""
    cache_key = f"{url}:{page_hash}:{taxonomy_version}:{cache_key_extra}{hint_suffix}"
    
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
        f"offering_type: {', '.join(taxonomy['offering_type'].keys())}",
        f"functions: {', '.join(taxonomy['functions'].keys())}",
        f"industries: {', '.join(taxonomy['industries'].keys())}",
        f"form: {', '.join(taxonomy['form'].keys())}",
        f"primary_class: {', '.join(taxonomy['primary_class'].keys())}",
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
        raise ValueError("No tool call returned from LLM")
    
    # Validate evidence and cap confidence for unsupported facts
    validated_products = []
    for product in tool_result.get("products", []):
        validated = validate_and_cap_confidence(product, page_text)
        validated_products.append(validated)
    
    return {
        "products": validated_products,
        "extraction_metadata": {
            "taxonomy_version": taxonomy_version,
            "cache_key": cache_key,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": response.model,
        }
    }
