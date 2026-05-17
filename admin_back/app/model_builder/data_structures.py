from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KeyInfoInstance(BaseModel):
    """
    Represents a single structured piece of information extracted from the raw text. (Layer 0)
    """
    idx: str
    day_id: int
    type: str = ""
    WHAT: str = ""
    WHEN: Dict[str, Any]
    WHERE: str = ""
    # FIX: Set default empty strings for optional fields (WHO, WHY, HOW)
    # This matches the "KEY_INFO_EXTRACTION" prompt which states these fields are optional.
    # The original code caused a pydantic validation error when the LLM omitted them.
    WHO: str = ""
    WHY: str = ""
    HOW: str = ""

class KnowledgeNode(BaseModel):
    """
    The fundamental unit of the cognitive model graph (Layer 1 and above).
    """
    node_id: str
    layer: int
    title: str
    content: str
    source_instances: List[str] = Field(default_factory=list)
    source_nodes: List[str] = Field(default_factory=list)
    generating_dimension: Optional[str] = Field(default=None)

class Dimension(BaseModel):
    """
    Represents an analytical "lens" for synthesizing higher-level knowledge.
    """
    title: str
    description: str
