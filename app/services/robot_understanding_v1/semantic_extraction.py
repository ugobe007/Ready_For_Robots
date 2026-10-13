"""
Semantic Extraction Engine for Robot Understanding v1.

Replaces regex pattern matching with LLM-based structured extraction:
- Single LLM call per page with strict JSON schema
- Confidence scores + provenance snippets for each fact
- Ontology mapping with gap logging
- URL + page-hash caching to avoid re-extraction

Design principles:
1. Low-confidence output stays low-confidence (no forcing vague copy into domains)
2. Unmapped terms logged as ontology gaps, not dropped
3. Regex kept as fast pre-pass / sanity check
4. Results cached by (url, sha256(page_text))

Schema:
{
  "product_class": str,           # e.g. "mobile_robot", "humanoid", "fixed_arm"
  "product_class_confidence": float,  # 0.0-1.0
  "product_class_evidence": str,      # snippet from page
  
  "domains": [                    # e.g. ["healthcare", "warehouse"]
    {"domain": str, "confidence": float, "evidence": str}
  ],
  
  "tasks": [                      # What the robot does
    {"task": str, "confidence": float, "evidence": str}
  ],
  
  "capabilities": [               # Hardware + software capabilities
    {"capability": str, "confidence": float, "evidence": str}
  ],
  
  "deployment_environment": [     # Where it operates
    {"environment": str, "confidence": float, "evidence": str}
  ],
  
  "buyer_verticals": [            # Target customers
    {"vertical": str, "confidence": float, "evidence": str}
  ],
  
  "hardware_properties": [        # Physical specs
    {"property": str, "value": str, "confidence": float, "evidence": str}
  ]
}

Ontology mapping:
- Map extracted terms to ontology/rfr_graph.v1.json predicates
- Log gaps when no ontology match exists
- Preserve original term + confidence even when unmapped
"""
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

import anthropic


@dataclass
class ExtractedFact:
    """Single extracted fact with confidence and provenance."""
    
    value: str
    confidence: float  # 0.0 - 1.0
    evidence: str  # Text snippet from page
    ontology_term: str | None = None  # Mapped ontology predicate
    ontology_gap: bool = False  # True if no ontology match


@dataclass
class SemanticExtractionResult:
    """Result of semantic extraction for one robot page."""
    
    url: str
    page_hash: str  # sha256(page_text)
    
    # Core classification
    product_class: ExtractedFact | None
    
    # Multi-value fields
    domains: list[ExtractedFact]
    tasks: list[ExtractedFact]
    capabilities: list[ExtractedFact]
    deployment_environments: list[ExtractedFact]
    buyer_verticals: list[ExtractedFact]
    hardware_properties: list[tuple[str, ExtractedFact]]  # (property_name, value_fact)
    
    # Metadata
    extraction_model: str
    extraction_timestamp: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for caching/logging."""
        return {
            "url": self.url,
            "page_hash": self.page_hash,
            "product_class": {
                "value": self.product_class.value,
                "confidence": self.product_class.confidence,
                "evidence": self.product_class.evidence,
                "ontology_term": self.product_class.ontology_term,
                "ontology_gap": self.product_class.ontology_gap,
            } if self.product_class else None,
            "domains": [
                {
                    "value": f.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "ontology_term": f.ontology_term,
                    "ontology_gap": f.ontology_gap,
                }
                for f in self.domains
            ],
            "tasks": [
                {
                    "value": f.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "ontology_term": f.ontology_term,
                    "ontology_gap": f.ontology_gap,
                }
                for f in self.tasks
            ],
            "capabilities": [
                {
                    "value": f.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "ontology_term": f.ontology_term,
                    "ontology_gap": f.ontology_gap,
                }
                for f in self.capabilities
            ],
            "deployment_environments": [
                {
                    "value": f.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "ontology_term": f.ontology_term,
                    "ontology_gap": f.ontology_gap,
                }
                for f in self.deployment_environments
            ],
            "buyer_verticals": [
                {
                    "value": f.value,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "ontology_term": f.ontology_term,
                    "ontology_gap": f.ontology_gap,
                }
                for f in self.buyer_verticals
            ],
            "hardware_properties": [
                {
                    "property": prop,
                    "value": fact.value,
                    "confidence": fact.confidence,
                    "evidence": fact.evidence,
                    "ontology_term": fact.ontology_term,
                    "ontology_gap": fact.ontology_gap,
                }
                for prop, fact in self.hardware_properties
            ],
            "extraction_model": self.extraction_model,
            "extraction_timestamp": self.extraction_timestamp,
        }


def compute_page_hash(page_text: str) -> str:
    """Compute SHA256 hash of page content for caching."""
    return sha256(page_text.encode("utf-8")).hexdigest()


def extract_robot_facts_semantic(
    url: str,
    page_text: str,
    *,
    model: str = "claude-opus-4-20250514",
    cache_key: str | None = None,
) -> SemanticExtractionResult:
    """
    Extract robot facts using LLM with structured output.
    
    Args:
        url: Robot page URL
        page_text: Plain text content
        model: LLM model to use
        cache_key: Optional cache key (url, page_hash) to check before extraction
        
    Returns:
        SemanticExtractionResult with all extracted facts + confidence + evidence
    """
    import json
    import os
    from datetime import datetime
    
    page_hash = compute_page_hash(page_text)
    
    # TODO: Check cache before extraction
    
    # Build extraction prompt
    extraction_schema = {
        "product_class": {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "Robot product class: mobile_robot, humanoid, fixed_arm, service_robot, etc."},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence score 0.0-1.0"},
                "evidence": {"type": "string", "description": "Exact text snippet from page supporting this classification"},
            },
            "required": ["value", "confidence", "evidence"],
        },
        "domains": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "Application domain: healthcare, warehouse, manufacturing, construction, hospitality, retail, etc."},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["value", "confidence", "evidence"],
            },
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "Task the robot performs: material_transport, picking, inspection, delivery, cleaning, etc."},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["value", "confidence", "evidence"],
            },
        },
        "capabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "Hardware/software capability: autonomous_navigation, obstacle_avoidance, gripper, vision_system, etc."},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["value", "confidence", "evidence"],
            },
        },
        "deployment_environments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "Where it operates: indoor, outdoor, hospital, warehouse_floor, factory_floor, construction_site, etc."},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["value", "confidence", "evidence"],
            },
        },
        "buyer_verticals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "Target buyer industry/vertical"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["value", "confidence", "evidence"],
            },
        },
        "hardware_properties": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "property": {"type": "string", "description": "Property name: payload_kg, speed_mps, battery_hours, height_cm, etc."},
                    "value": {"type": "string", "description": "Property value with units"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["property", "value", "confidence", "evidence"],
            },
        },
    }
    
    prompt = f"""Extract structured facts about this robot from the page text.

URL: {url}

Page text:
{page_text[:8000]}

Extract the following information with confidence scores (0.0-1.0) and exact evidence snippets:

1. Product class (mobile_robot, humanoid, fixed_arm, service_robot, cobot, etc.)
2. Domains (healthcare, warehouse, manufacturing, construction, hospitality, retail, agriculture, etc.)
3. Tasks it performs (picking, transport, delivery, inspection, cleaning, assembly, welding, etc.)
4. Capabilities (autonomous_navigation, obstacle_avoidance, gripper, vision_system, speech, manipulation, etc.)
5. Deployment environments (indoor, outdoor, hospital, warehouse_floor, factory_floor, construction_site, etc.)
6. Buyer verticals (target customer industries)
7. Hardware properties (payload, speed, battery life, dimensions, etc.)

Guidelines:
- Use low confidence (0.3-0.5) for vague marketing copy like "AI-powered" or "flexible automation"
- Use medium confidence (0.6-0.8) for specific but not quantified claims
- Use high confidence (0.9-1.0) only for concrete, specific, quantified facts
- Include exact text snippets as evidence (20-50 words)
- If something is not mentioned, omit it (don't invent)
- Preserve technical terminology from the page

Return JSON matching this schema:
{json.dumps(extraction_schema, indent=2)}"""
    
    # Call LLM
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    
    # Parse response
    response_text = response.content[0].text
    
    # Extract JSON from response (may be wrapped in markdown)
    if "```json" in response_text:
        json_start = response_text.index("```json") + 7
        json_end = response_text.index("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.index("```") + 3
        json_end = response_text.index("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    else:
        json_text = response_text
    
    extracted = json.loads(json_text)
    
    # Map to ontology and build result
    product_class_raw = extracted.get("product_class")
    product_class_fact = None
    if product_class_raw:
        ontology_term = map_to_ontology(product_class_raw["value"], "product_class")
        if ontology_term is None:
            log_ontology_gap(product_class_raw["value"], "product_class", url)
        product_class_fact = ExtractedFact(
            value=product_class_raw["value"],
            confidence=product_class_raw["confidence"],
            evidence=product_class_raw["evidence"],
            ontology_term=ontology_term,
            ontology_gap=ontology_term is None,
        )
    
    def map_list(items: list[dict], category: str) -> list[ExtractedFact]:
        facts = []
        for item in items:
            ontology_term = map_to_ontology(item["value"], category)
            if ontology_term is None:
                log_ontology_gap(item["value"], category, url)
            facts.append(ExtractedFact(
                value=item["value"],
                confidence=item["confidence"],
                evidence=item["evidence"],
                ontology_term=ontology_term,
                ontology_gap=ontology_term is None,
            ))
        return facts
    
    domains = map_list(extracted.get("domains", []), "domain")
    tasks = map_list(extracted.get("tasks", []), "task")
    capabilities = map_list(extracted.get("capabilities", []), "capability")
    deployment_envs = map_list(extracted.get("deployment_environments", []), "deployment_environment")
    buyer_verticals = map_list(extracted.get("buyer_verticals", []), "buyer_vertical")
    
    hardware_props = []
    for hw in extracted.get("hardware_properties", []):
        ontology_term = map_to_ontology(hw["property"], "hardware_property")
        if ontology_term is None:
            log_ontology_gap(hw["property"], "hardware_property", url)
        hardware_props.append((
            hw["property"],
            ExtractedFact(
                value=hw["value"],
                confidence=hw["confidence"],
                evidence=hw["evidence"],
                ontology_term=ontology_term,
                ontology_gap=ontology_term is None,
            ),
        ))
    
    result = SemanticExtractionResult(
        url=url,
        page_hash=page_hash,
        product_class=product_class_fact,
        domains=domains,
        tasks=tasks,
        capabilities=capabilities,
        deployment_environments=deployment_envs,
        buyer_verticals=buyer_verticals,
        hardware_properties=hardware_props,
        extraction_model=model,
        extraction_timestamp=datetime.utcnow().isoformat() + "Z",
    )
    
    # TODO: Cache result
    
    return result


def map_to_ontology(term: str, category: str) -> str | None:
    """
    Map extracted term to ontology predicate.
    
    Args:
        term: Extracted term (e.g. "mobile manipulator")
        category: Category (e.g. "product_class", "capability", "domain")
        
    Returns:
        Ontology predicate or None if no match
    """
    import json
    from pathlib import Path
    
    # Load ontology
    ontology_path = Path(__file__).parent.parent.parent.parent / "ontology" / "rfr_graph.v1.json"
    if not ontology_path.exists():
        return None
    
    with open(ontology_path, "r") as f:
        ontology = json.load(f)
    
    # Normalize term
    term_lower = term.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Category-specific mapping
    if category == "product_class":
        # Check robot_types in ontology
        robot_types = ontology.get("nodes", {}).get("robot_types", [])
        for rt in robot_types:
            rt_name = rt.get("name", "").lower().replace(" ", "_")
            if term_lower in rt_name or rt_name in term_lower:
                return rt.get("id") or rt_name
        
        # Common aliases
        aliases = {
            "mobile_robot": "mobile_robot",
            "amr": "mobile_robot",
            "autonomous_mobile_robot": "mobile_robot",
            "humanoid": "humanoid_robot",
            "humanoid_robot": "humanoid_robot",
            "cobot": "collaborative_robot",
            "collaborative_robot": "collaborative_robot",
            "fixed_arm": "robotic_arm",
            "robotic_arm": "robotic_arm",
            "industrial_arm": "robotic_arm",
            "service_robot": "service_robot",
            "delivery_robot": "delivery_robot",
        }
        return aliases.get(term_lower)
    
    elif category == "domain":
        # Domain predicates
        domains = {
            "healthcare": "healthcare_domain",
            "hospital": "healthcare_domain",
            "medical": "healthcare_domain",
            "warehouse": "warehouse_domain",
            "logistics": "warehouse_domain",
            "fulfillment": "warehouse_domain",
            "manufacturing": "manufacturing_domain",
            "factory": "manufacturing_domain",
            "industrial": "manufacturing_domain",
            "construction": "construction_domain",
            "jobsite": "construction_domain",
            "hospitality": "hospitality_domain",
            "hotel": "hospitality_domain",
            "restaurant": "hospitality_domain",
            "retail": "retail_domain",
            "store": "retail_domain",
            "agriculture": "agriculture_domain",
            "farming": "agriculture_domain",
        }
        return domains.get(term_lower)
    
    elif category == "capability":
        # Check capabilities in ontology
        capabilities = ontology.get("edges", {}).get("capabilities", [])
        for cap in capabilities:
            cap_name = cap.get("name", "").lower().replace(" ", "_")
            if term_lower in cap_name or cap_name in term_lower:
                return cap.get("id") or cap_name
        
        # Common capability aliases
        cap_aliases = {
            "autonomous_navigation": "autonomous_navigation",
            "navigation": "autonomous_navigation",
            "obstacle_avoidance": "obstacle_avoidance",
            "collision_avoidance": "obstacle_avoidance",
            "gripper": "grasping",
            "grasping": "grasping",
            "manipulation": "manipulation",
            "picking": "object_picking",
            "object_picking": "object_picking",
            "vision": "computer_vision",
            "computer_vision": "computer_vision",
            "visual_perception": "computer_vision",
            "speech": "speech_recognition",
            "voice": "speech_recognition",
        }
        return cap_aliases.get(term_lower)
    
    elif category == "task":
        # Task predicates
        tasks = {
            "material_transport": "material_transport",
            "transport": "material_transport",
            "delivery": "delivery",
            "picking": "picking",
            "object_picking": "picking",
            "inspection": "inspection",
            "quality_inspection": "inspection",
            "cleaning": "cleaning",
            "disinfection": "cleaning",
            "assembly": "assembly",
            "welding": "welding",
            "palletizing": "palletizing",
            "depalletizing": "depalletizing",
        }
        return tasks.get(term_lower)
    
    elif category == "deployment_environment":
        envs = {
            "indoor": "indoor_environment",
            "outdoor": "outdoor_environment",
            "hospital": "hospital_environment",
            "warehouse": "warehouse_environment",
            "warehouse_floor": "warehouse_environment",
            "factory": "factory_environment",
            "factory_floor": "factory_environment",
            "construction_site": "construction_environment",
            "jobsite": "construction_environment",
        }
        return envs.get(term_lower)
    
    elif category == "hardware_property":
        props = {
            "payload": "payload_capacity",
            "payload_kg": "payload_capacity",
            "speed": "max_speed",
            "speed_mps": "max_speed",
            "battery": "battery_life",
            "battery_hours": "battery_life",
            "height": "height",
            "height_cm": "height",
            "weight": "weight",
            "weight_kg": "weight",
        }
        return props.get(term_lower)
    
    # No match found
    return None


def log_ontology_gap(term: str, category: str, url: str) -> None:
    """
    Log a term that has no ontology mapping.
    
    These gaps should be reviewed and either:
    1. Added to the ontology
    2. Mapped to existing ontology terms
    3. Marked as noise/irrelevant
    """
    import json
    from datetime import datetime
    from pathlib import Path
    
    gap_log_path = Path(__file__).parent / "ontology_gaps.jsonl"
    
    gap_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "url": url,
        "category": category,
        "term": term,
    }
    
    # Append to JSONL file
    try:
        with open(gap_log_path, "a") as f:
            f.write(json.dumps(gap_entry) + "\n")
    except Exception:
        # Don't fail extraction if logging fails
        pass
