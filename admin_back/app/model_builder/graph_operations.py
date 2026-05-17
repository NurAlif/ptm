import os
import json
import time
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy.spatial.distance import cosine

# --- NEW IMPORTS ---
from gemini_api_client import query_api_with_retries, MODEL_LITE
from .logging_context import get_current_logger
# --- END NEW IMPORTS ---

from . import config, llm_handler, prompts
from .data_structures import KnowledgeNode, KeyInfoInstance, Dimension

embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        try:
            print("[Graph Ops] Loading sentence transformer model (lazy)...")
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            print("[Graph Ops] Model loaded.")
        except Exception as e:
            print(f"[Graph Ops] WARNING: Could not load embedding model. Similarity search disabled. Error: {e}")
    return embedding_model

def create_nodes_from_cluster(instances: List[KeyInfoInstance], layer: int, cluster_index: int) -> List[KnowledgeNode]:
    """
    Generates one or more KnowledgeNodes from a cluster of instances using an LLM call.
    The prompt now supports returning 1-3 nodes per cluster.
    (Refactored to use query_api_with_retries)
    """
    logger = get_current_logger() # Get the logger

    # --- START NEW FIX ---
    # Filter instances to only include those with actual content.
    # The 'WHAT' field is the most critical for this prompt.
    valid_instances = [inst for inst in instances if inst.WHAT and inst.WHAT.strip()]
    
    if not valid_instances:
        logger.warning(f"  [WARN] Skipping cluster {cluster_index} because it contains no instances with valid 'WHAT' content.")
        return []
    # --- END NEW FIX ---

    # --- Use valid_instances from now on ---
    instance_ids = [inst.idx for inst in valid_instances]

    # --- Create comprehensive instance text with all 5W1H info ---
    instances_text_parts = []
    for inst in valid_instances: # <-- Use valid_instances
        when_str = json.dumps(inst.WHEN)
        full_info_parts = []
        if inst.WHAT: full_info_parts.append(f"WHAT: {inst.WHAT}")
        if inst.WHEN: full_info_parts.append(f"WHEN: {when_str}")
        if inst.WHERE: full_info_parts.append(f"WHERE: {inst.WHERE}")
        if inst.WHO: full_info_parts.append(f"WHO: {inst.WHO}")
        if inst.WHY: full_info_parts.append(f"WHY: {inst.WHY}")
        if inst.HOW: full_info_parts.append(f"HOW: {inst.HOW}")

        full_info = ", ".join(full_info_parts)
        instances_text_parts.append(f"- (ID: {inst.idx}) {full_info}")
    
    instances_text = "\\n".join(instances_text_parts)
    # --- END ---

    prompt = prompts.DIRECT_INFERENCE_GENERATION.format(
        instance_ids_json=json.dumps(instance_ids),
        instances_text=instances_text
    )
    task_desc = f"Synthesize L{layer} Node(s) from cluster {cluster_index}"

    # --- START REFACTOR ---
    # Replace _call_llm and _parse_json_response with a single call
    
    new_nodes: List[KnowledgeNode] = []
    
    try:
        time.sleep(3)
        data = query_api_with_retries(
            prompt=prompt,
            model=MODEL_LITE,
            outjson=True
        )
        
        # Case 1: LLM returns a list of nodes (correct new behavior)
        if isinstance(data, list):
            # --- START FIX ---
            # Added enumerate and a type check for 'item'
            for i, item in enumerate(data):
                # Check if the item is a dictionary before trying to access it
                if not isinstance(item, dict):
                    logger.warning(f"  [WARN] Skipping malformed item #{i} from LLM for cluster {cluster_index}. Expected dict, got {type(item)}: {item}")
                    continue
                # --- END FIX ---
                
                if all(k in item for k in ["title", "content", "source_instances"]):
                    new_nodes.append(KnowledgeNode(
                        node_id=f"L{layer}_Node_TEMP", # Temporary ID, will be finalized in router
                        layer=layer,
                        title=item["title"],
                        content=item["content"],
                        source_instances=item["source_instances"],
                        source_nodes=[]
                    ))
                else:
                    logger.warning(f"  [WARN] A synthesized node from cluster {cluster_index} was malformed and skipped: {item}")
                    
        # Case 2: LLM fails and returns a single object (old behavior)
        elif isinstance(data, dict) and all(k in data for k in ["title", "content", "source_instances"]):
            logger.warning(f"  [WARN] LLM returned a single object instead of a list for cluster {cluster_index}. Wrapping it.")
            new_nodes.append(KnowledgeNode(
                node_id=f"L{layer}_Node_TEMP",
                layer=layer,
                title=data["title"],
                content=data["content"],
                source_instances=data["source_instances"],
                source_nodes=[]
            ))
        
        elif data:
             logger.warning(f"  [WARN] LLM response for cluster {cluster_index} was not a list or valid node object. Skipping.")

    except Exception as e:
        logger.error(f"  [LLM Call] Error processing task '{task_desc}': {e}", exc_info=True)
        # Return empty list on failure
        return []

    # --- END REFACTOR ---

    return new_nodes

# --- REMOVED FUNCTION ---
# This function is no longer called by the router (app/routers/models.py).
# The router now correctly calls `llm_handler.synthesize_nodes_for_dimension` instead.
# This function is now dead code and can be removed.
#
# def create_nodes_from_synthesis(source_nodes: List[KnowledgeNode], dimension: Dimension, layer: int) -> List[KnowledgeNode]:
#     ...
# --- END REMOVED FUNCTION ---


def save_graph_layer(nodes: List[KnowledgeNode], layer: int, output_dir: str):
    filepath = os.path.join(output_dir, f"L{layer}_nodes.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([node.dict() for node in nodes], f, indent=2)
    print(f"[SAVE] Saved L{layer} graph with {len(nodes)} nodes to '{filepath}'")

def save_dimensions_for_layer(dimensions: List[Dimension], layer: int, output_dir: str):
    filepath = os.path.join(output_dir, f"L{layer}_dimensions.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([dim.dict() for dim in dimensions], f, indent=2)
    print(f"[SAVE] Saved {len(dimensions)} dimensions for L{layer} to '{filepath}'")

def load_graph_layer(layer: int, user_output_dir: str) -> List[KnowledgeNode]:
    """Loads a list of KnowledgeNodes from a JSON file for a specific layer."""
    # --- FIX: Use user_output_dir, not global config ---
    filepath = os.path.join(user_output_dir, f"L{layer}_nodes.json")
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [KnowledgeNode(**item) for item in data]

def find_most_similar_node(
    new_instances: List[KeyInfoInstance],
    existing_nodes: List[KnowledgeNode]
) -> Tuple[Optional[KnowledgeNode], float]:
    """
    Finds the most semantically similar existing node to a new cluster of instances.
    (Phase 3, Step 7)
    """
    logger = get_current_logger() # Get logger
    if not new_instances or not existing_nodes:
        return None, 0.0
        
    model = get_embedding_model()
    if not model:
        logger.error("[Graph Ops] Similarity search failed: Embedding model not loaded.")
        return None, 0.0

    logger.info(f"  - Comparing {len(new_instances)} new instance(s) against {len(existing_nodes)} existing L1 nodes.")
    # Create a summary of the new instances to embed
    new_cluster_summary = ". ".join([inst.WHAT for inst in new_instances])

    # Get embeddings
    new_embedding = model.encode(new_cluster_summary)
    existing_embeddings = model.encode([node.content for node in existing_nodes])

    # Calculate cosine similarities (1 - cosine distance)
    similarities = 1 - np.array([cosine(new_embedding, emb) for emb in existing_embeddings])

    best_match_index = np.argmax(similarities)
    max_similarity = similarities[best_match_index]

    logger.info(f"    - Best match is node '{existing_nodes[best_match_index].title}' with similarity score: {max_similarity:.4f}")

    return existing_nodes[best_match_index], float(max_similarity)