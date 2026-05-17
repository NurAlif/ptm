from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Body
from fastapi.responses import StreamingResponse, JSONResponse
from ..database import Session
from typing import List, Dict, Any
import os
import json
import re
import asyncio
import random
import logging
import importlib
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime 
import glob 

from .. import database, schemas, models, security
from ..database import get_db

# Import the model builder logic
from ..model_builder import llm_handler, clustering, graph_operations as graph_ops
from ..model_builder import config as model_config
from ..model_builder.data_structures import KeyInfoInstance, KnowledgeNode, Dimension
from ..model_builder import prompts as default_prompts_module
from ..model_builder.logging_context import user_logger_context


router = APIRouter(
    prefix="/models",
    tags=["Models"],
)



# --- Default Config ---
DEFAULT_CONFIG = {
    "TOTAL_LAYERS": model_config.TOTAL_LAYERS,
    "GEMINI_MODEL_NAME": model_config.GEMINI_MODEL_NAME,
    "API_MAX_RETRIES": model_config.API_MAX_RETRIES,
    "API_RETRY_DELAY": model_config.API_RETRY_DELAY,
    "API_REQUEST_DELAY": model_config.API_REQUEST_DELAY,
    "MAX_OUTPUT_TOKENS": model_config.MAX_OUTPUT_TOKENS,
    "EMBEDDING_MODEL": model_config.EMBEDDING_MODEL,
    "UMAP_N_COMPONENTS": model_config.UMAP_N_COMPONENTS,
    "UMAP_N_NEIGHBORS": model_config.UMAP_N_NEIGHBORS,
    "UMAP_MIN_DIST": model_config.UMAP_MIN_DIST,
    "HDBSCAN_MIN_CLUSTER_SIZE": model_config.HDBSCAN_MIN_CLUSTER_SIZE,
    "MAX_CLUSTER_SIZE": model_config.MAX_CLUSTER_SIZE,
    "KMEANS_SPLIT_FACTOR": model_config.KMEANS_SPLIT_FACTOR,
    "FINAL_MIN_RECURRENCE": model_config.FINAL_MIN_RECURRENCE,
    "FINAL_MIN_CLUSTER_SIZE": model_config.FINAL_MIN_CLUSTER_SIZE,
    "DIMENSION_SAMPLE_SIZE": model_config.DIMENSION_SAMPLE_SIZE,
    "NUM_DIMENSIONS_PER_LAYER": model_config.NUM_DIMENSIONS_PER_LAYER,
    "SIMILARITY_THRESHOLD": model_config.SIMILARITY_THRESHOLD,
    # --- Control 'm' (clusters per dimension) ---
    "TARGET_CLUSTERS_PER_DIMENSION": 0,
    # --- Per-Layer Control ---
    "TARGET_CLUSTERS_BY_LAYER": {
        "L2": 0,
        "L3": 0,
        "L4": 0
    }
}


DATASETS_DIR = model_config.OUTPUT_DIR
build_processes: Dict[int, bool] = {}

def setup_user_logger(user_id: int):
    """Sets up a dedicated file logger for a user's build process."""
    user_output_dir = os.path.join(DATASETS_DIR, str(user_id))
    os.makedirs(user_output_dir, exist_ok=True)
    log_file = os.path.join(user_output_dir, 'build.log')

    logger = logging.getLogger(f"user_{user_id}_build")
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG) 
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=1) 
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def run_model_pipeline_for_user(user_id: int, build_mode: str):
    """
    Runs the full model generation pipeline synchronously in a background thread.
    """
    logger = setup_user_logger(user_id)
    user_output_dir = os.path.join(DATASETS_DIR, str(user_id))
    status_file = os.path.join(user_output_dir, 'build_status.json')
    
    # --- Load Config & Apply Overrides ---
    logger.info("INFO: Loading model configuration...")
    user_config_file = os.path.join(user_output_dir, 'model_config.json')
    dynamic_config = DEFAULT_CONFIG.copy() 
    
    if os.path.exists(user_config_file):
        try:
            with open(user_config_file, 'r') as f:
                user_config_data = json.load(f)
            logger.info("INFO: Found user-defined model_config.json. Applying overrides...")
            dynamic_config.update(user_config_data) 
            for key, value in user_config_data.items():
                if key in DEFAULT_CONFIG:
                    logger.info(f"  - Override: {key} = {value}")
        except Exception as e:
            logger.error(f"ERROR: Failed to load or apply user config, using defaults. Error: {e}")
    else:
        logger.info("INFO: No user-defined config found, using defaults.")
    
    # --- Apply to model_config module ---
    # FIX: Removed the 'if hasattr' check to allow injecting new keys
    logger.info("INFO: Applying dynamic configuration to model_config module...")
    applied_count = 0
    for key, value in dynamic_config.items():
        try:
            original_value = getattr(model_config, key, None)
            setattr(model_config, key, value)
            if original_value != value:
                logger.info(f"  - Applied override: {key} = {value} (was {original_value})")
                applied_count += 1
        except Exception as e:
            logger.error(f"  - FAILED to apply override for {key}: {e}")

    if applied_count == 0:
        logger.info("INFO: Dynamic config matched defaults. No overrides applied.")
    else:
        logger.info(f"INFO: Successfully applied {applied_count} configuration overrides.")
    
    total_layers_from_config = dynamic_config.get("TOTAL_LAYERS", model_config.TOTAL_LAYERS)
    logger.info(f"INFO: Build will run up to TOTAL_LAYERS = {total_layers_from_config}")
    
    # --- Ensure Default Prompts Loaded ---
    try:
        importlib.reload(default_prompts_module)
        logger.info("INFO: Standard system prompts successfully loaded.")
    except Exception as e:
        logger.error(f"ERROR: Failed to reload system prompts: {e}")


    def write_status(status: str, error: str = None):
        with open(status_file, 'w') as f:
            json.dump({"status": status, "error": error}, f)

    db = None

    try:
        with user_logger_context(logger):
            write_status("running")
            logger.info(f"INFO: Starting Model Pipeline for User ID: {user_id}")
            logger.info(f"INFO: Build Mode selected: {build_mode}")
            
            db = database.SessionLocal() 
            
            l0_raw_file = os.path.join(user_output_dir, 'L0_raw_keyinfo.json')
            l0_formatted_file = os.path.join(user_output_dir, 'L0_keyinfo_instances.json')
            l1_clusters_file = os.path.join(user_output_dir, 'L1_consensus_clusters.json')
            l1_nodes_file = os.path.join(user_output_dir, 'L1_nodes.json')

            temp_instances_data: Optional[List[Dict[str, Any]]] = None
            all_instances: Optional[List[KeyInfoInstance]] = None
            instance_clusters: Optional[Dict[str, List[str]]] = None
            current_layer_nodes: Optional[List[KnowledgeNode]] = None
            
            # --- Step 1: Get L0 Raw KeyInfo ---
            if not os.path.exists(l0_raw_file) or build_mode == "rebuild_full":
                logger.info("PHASE 1 (Step 1): No raw keyinfo file found. Starting from raw data...")
                
                base_query = db.query(models.Journal).filter(
                    models.Journal.user_id == user_id,
                    models.Journal.writing_phase == models.JournalPhase.completed,
                    models.Journal.content != None,
                    models.Journal.content != ''
                )
                
                total_journal_count = base_query.count()
                logger.info(f"INFO: Found {total_journal_count} total completed journals for user {user_id}.")

                JOURNALS_TO_EXCLUDE = 7
                limit_count = total_journal_count - JOURNALS_TO_EXCLUDE
                
                if limit_count <= 0:
                    raise Exception(f"Not enough journals. Found {total_journal_count}, but need more than {JOURNALS_TO_EXCLUDE} to build a model (excluding the last 7).")

                logger.info(f"INFO: Excluding the last {JOURNALS_TO_EXCLUDE} journals. Using the first {limit_count} journals for model building.")
                
                journals = base_query.order_by(models.Journal.journal_date.asc()).limit(limit_count).all()

                if not journals:
                    raise Exception(f"No completed journals found for user {user_id} after applying limit. Aborting.")

                logger.info(f"INFO: Processing {len(journals)} journals for model building...")
                
                temp_instances_data = []
                for i, journal in enumerate(journals):
                    journal_date_str = journal.journal_date.strftime("%A, %B %d, %Y")
                    journal_title = journal.title or "Untitled Journal"
                    context_header = f"Journal Entry for {journal_date_str}\nTitle: {journal_title}\n\n---\n\n"
                    context_footer = f"\n\n---\nNote: The context for this entry is {journal_date_str}."
                    entry = context_header + (journal.content or "") + context_footer

                    if not journal.content or not journal.content.strip():
                        continue 
                    
                    logger.info(f"  - Processing journal entry {i+1}/{len(journals)} (Date: {journal.journal_date})...")
                    keyinfo_list = llm_handler.extract_key_info(entry)
                    
                    for j, info in enumerate(keyinfo_list):
                        if not isinstance(info, dict):
                            logger.warning(f"  [WARN] Skipping malformed instance from LLM for journal {i+1}. Expected dict, got {type(info)}: {info}")
                            continue

                        instance_id = f"keyinfo-{j}_raw-{i}"
                        temp_instances_data.append({
                            'id': instance_id,
                            'day_id': i,
                            'date': journal_date_str, 
                            'data': info
                        })
                
                logger.info(f"PHASE 1 (Step 1): Saving {len(temp_instances_data)} raw instances to '{l0_raw_file}'...")
                with open(l0_raw_file, 'w', encoding='utf-8') as f:
                    json.dump(temp_instances_data, f, indent=2)
            else:
                logger.info(f"PHASE 1 (Step 1): Loading raw keyinfo from cache: {l0_raw_file}")
                with open(l0_raw_file, 'r', encoding='utf-8') as f:
                    temp_instances_data = json.load(f)

            # --- Step 2: Get L0 Formatted Instances ---
            if not os.path.exists(l0_formatted_file) or build_mode in ["rebuild_full", "rebuild_l1_up"]:
                logger.info("PHASE 1 (Step 2): No formatted instances file found. Running batch time formatting...")
                if not temp_instances_data:
                    raise Exception("L0 raw keyinfo data is missing. Cannot proceed with time formatting.")

                logger.info(f"PHASE 1: Collected {len(temp_instances_data)} raw instances. Now batch formatting time strings...")
                
                time_strings_to_format = {
                    item['id']: f"{item['data'].get('WHEN', '')} (Context: {item['date']})"
                    for item in temp_instances_data
                }
                
                formatted_times = {}
                batch_size = 10 
                items_to_process = list(time_strings_to_format.items())
                
                for i in range(0, len(items_to_process), batch_size):
                    batch_items = items_to_process[i:i + batch_size]
                    batch_dict = dict(batch_items)
                    
                    if not batch_dict: continue

                    logger.info(f"  - Formatting time batch {i//batch_size + 1}/{(len(items_to_process) + batch_size - 1)//batch_size}...")
                    batch_results = llm_handler.format_time_batch(batch_dict)
                    formatted_times.update(batch_results)
                    
                logger.info("PHASE 1: Time formatting complete.")

                all_instances = []
                for item in temp_instances_data:
                    instance_id = item['id']
                    info = item['data']
                    instance_type = info.pop('type', 'Unknown')
                    info.pop('WHEN', None) 
                    final_formatted_time = formatted_times.get(instance_id, {})
                    
                    instance = KeyInfoInstance(
                        idx=instance_id, day_id=item['day_id'], type=instance_type,
                        WHEN=final_formatted_time, **info
                    )
                    all_instances.append(instance)
                    
                logger.info(f"PHASE 1 (Step 2): Created {len(all_instances)} final key instances.")
                
                if not all_instances:
                    raise Exception("No key instances were created after time formatting. Cannot proceed.")

                with open(l0_formatted_file, 'w', encoding='utf-8') as f:
                    json.dump([inst.dict() for inst in all_instances], f, indent=2)
                logger.info(f"PHASE 1 (Step 2): Saved {len(all_instances)} L0 instances to '{l0_formatted_file}'.")
            else:
                logger.info(f"PHASE 1 (Step 2): Loading formatted instances from cache: {l0_formatted_file}")
                with open(l0_formatted_file, 'r', encoding='utf-8') as f:
                    all_instances = [KeyInfoInstance(**data) for data in json.load(f)]

            # --- Step 3: Get L1 Nodes ---
            if not os.path.exists(l1_nodes_file) or build_mode in ["rebuild_full", "rebuild_l1_up"]:
                logger.info("PHASE 1 (Step 3): No L1 nodes file found. Generating L1 nodes...")
                if not all_instances:
                    raise Exception("L0 formatted instances data is missing. Cannot generate L1.")

                if not os.path.exists(l1_clusters_file) or build_mode in ["rebuild_full", "rebuild_l1_up"]:
                    logger.info("INFO: No L1 clusters file found. Running clustering pipeline...")
                    instance_clusters = clustering.run_clustering_pipeline(all_instances, user_output_dir)
                else:
                    logger.info(f"INFO: Resuming from existing L1 clusters file: {l1_clusters_file}")
                    with open(l1_clusters_file, 'r', encoding='utf-8') as f:
                        instance_clusters = json.load(f)
                
                if not instance_clusters:
                    raise Exception("Clustering pipeline produced no clusters. Cannot generate L1 nodes.")

                logger.info(f"PHASE 1: Generating L1 knowledge graph from {len(instance_clusters)} clusters...")
                layer1_nodes: List[KnowledgeNode] = []
                
                for i, cluster_instance_ids in enumerate(instance_clusters.values()):
                    logger.info(f"  - Synthesizing L1 Node(s) from Cluster {i+1}/{len(instance_clusters)}...")
                    cluster_instances = [inst for inst in all_instances if inst.idx in cluster_instance_ids]
                    nodes = graph_ops.create_nodes_from_cluster(cluster_instances, 1, i)
                    
                    if nodes:
                        logger.info(f"    - Generated {len(nodes)} node(s) from this cluster.")
                        layer1_nodes.extend(nodes)
                    else:
                         logger.info(f"    - No nodes generated for this cluster.")
                
                logger.info(f"PHASE 1: Assigning final sequential IDs to {len(layer1_nodes)} new L1 nodes...")
                for i, node in enumerate(layer1_nodes):
                    node.node_id = f"L1_Node_{i}"
                
                graph_ops.save_graph_layer(layer1_nodes, 1, user_output_dir)
                logger.info(f"PHASE 1 (Step 3) COMPLETE: Saved L1 graph with {len(layer1_nodes)} nodes.")
                current_layer_nodes = layer1_nodes
            else:
                logger.info(f"PHASE 1 (Step 3): Loading L1 nodes from cache: {l1_nodes_file}")
                with open(l1_nodes_file, 'r', encoding='utf-8') as f:
                    current_layer_nodes = [KnowledgeNode(**data) for data in json.load(f)]
            
            # --- Step 4: Dimension Generation ---
            logger.info("PHASE 2 (Step 4): Generating all hierarchical dimensions (L2-L4)...")
            all_dimensions_data: Dict[str, List[Dimension]] = {}
            
            l1_nodes_for_sampling = current_layer_nodes
            if not l1_nodes_for_sampling:
                if os.path.exists(l1_nodes_file):
                    l1_nodes_for_sampling = graph_ops.load_graph_layer(1, user_output_dir)
                else:
                    raise Exception("Cannot generate dimensions: L1 nodes file is missing.")
            
            if l1_nodes_for_sampling:
                sample_size = min(len(l1_nodes_for_sampling), model_config.DIMENSION_SAMPLE_SIZE)
                logger.info(f"  - Sampling {sample_size} nodes from L1...")
                sample_nodes = random.sample(l1_nodes_for_sampling, sample_size)
                
                all_dimensions_data = llm_handler.generate_dimensions(sample_nodes, 1)
                
                graph_ops.save_dimensions_for_layer(all_dimensions_data.get("L2", []), 2, user_output_dir)
                graph_ops.save_dimensions_for_layer(all_dimensions_data.get("L3", []), 3, user_output_dir)
                graph_ops.save_dimensions_for_layer(all_dimensions_data.get("L4", []), 4, user_output_dir)
                logger.info("INFO: All hierarchical dimensions generated and saved.")
            else:
                logger.warning("WARN: No L1 nodes available for sampling. Cannot generate dimensions.")


            # --- Step 5: Higher Layer Generation Loop ---
            logger.info(f"PHASE 2 (Step 5): Building higher layers...")
            
            for i in range(2, total_layers_from_config + 1):
                l_i_nodes_file = os.path.join(user_output_dir, f'L{i}_nodes.json')
                
                if os.path.exists(l_i_nodes_file) and build_mode == "resume":
                    logger.info(f"PHASE 2: Loading L{i} nodes from cache: {l_i_nodes_file}")
                    with open(l_i_nodes_file, 'r', encoding='utf-8') as f:
                        current_layer_nodes = [KnowledgeNode(**data) for data in json.load(f)]
                    continue 

                if not current_layer_nodes:
                    logger.warning(f"WARN: Cannot build Layer {i} because Layer {i-1} is empty. Stopping.")
                    break
                
                logger.info(f"PHASE 2: Generating Layer {i}...")
                
                layer_key = f"L{i}"
                dimensions = all_dimensions_data.get(layer_key, [])
                
                if not dimensions:
                    # Fallback: Try to load dimensions from file if not in memory
                    dim_file = os.path.join(user_output_dir, f"L{i}_dimensions.json")
                    if os.path.exists(dim_file):
                        with open(dim_file, 'r') as f:
                            dim_data = json.load(f)
                            dimensions = [Dimension(**d) for d in dim_data]
                            logger.info(f"  - Loaded {len(dimensions)} dimensions from disk for {layer_key}.")
                    
                    if not dimensions:
                        logger.error(f"ERROR: No dimensions found or generated for {layer_key}. Cannot build this layer. Stopping.")
                        break 
                
                logger.info(f"  - Synthesizing L{i} nodes using {len(dimensions)} dimensions...")

                new_layer_nodes = []
                for dim in dimensions:
                    logger.info(f"    - Processing Dimension: '{dim.title}'")
                    
                    # 1. Cluster the previous layer's nodes
                    # Ensure 'layer=i' is passed so the handler knows which target to use
                    clusters = llm_handler.cluster_nodes_by_dimension(current_layer_nodes, dim, layer=i)
                    logger.info(f"      > Found {len(clusters)} clusters for this dimension.")

                    # 2. Iterate through clusters and synthesize
                    for cluster in clusters:
                        cluster_label = cluster['label']
                        cluster_nodes = cluster['nodes']
                        
                        if len(cluster_nodes) < 2:
                            continue
                            
                        logger.info(f"      - Synthesizing cluster: '{cluster_label}' ({len(cluster_nodes)} source nodes)...")
                        
                        nodes_data_list = llm_handler.synthesize_nodes_from_cluster(
                            cluster_nodes, 
                            cluster_label, 
                            dim, 
                            i
                        )
                        
                        if nodes_data_list:
                            for node_data in nodes_data_list:
                                new_node = KnowledgeNode(
                                    node_id="TEMP", 
                                    layer=i,
                                    **node_data
                                )
                                new_layer_nodes.append(new_node)
                                logger.info(f"        > Created Node: {new_node.title}")
                        else:
                            logger.info(f"        > No insights generated for this cluster.")

                for node_idx, node in enumerate(new_layer_nodes):
                    node.node_id = f"L{i}_Node_{node_idx}"
                
                graph_ops.save_graph_layer(new_layer_nodes, i, user_output_dir)
                logger.info(f"PHASE 2 COMPLETE: Saved L{i} graph with {len(new_layer_nodes)} nodes.")
                current_layer_nodes = new_layer_nodes

        logger.info("SUCCESS: Model build pipeline finished successfully.")
        write_status("completed")
    except Exception as e:
        error_message = f"FATAL ERROR: An unexpected error occurred in the pipeline: {e}"
        logger.error(error_message, exc_info=True) 
        write_status("failed", str(e))
    finally:
        if db:
            db.close()
        build_processes.pop(user_id, None)
        
        logger.info("INFO: Restoring default model_config module settings...")
        for key, value in DEFAULT_CONFIG.items():
             if hasattr(model_config, key):
                 setattr(model_config, key, value)
        logger.info("INFO: Default settings restored.")

# ... (Rest of the file including log_streamer and endpoints remains the same) ...
# I will include the full file content for completeness.

async def log_streamer(user_id: int):
    """Yields logs from a file as server-sent events (SSE)."""
    log_file = os.path.join(DATASETS_DIR, str(user_id), 'build.log')
    status_file = os.path.join(DATASETS_DIR, str(user_id), 'build_status.json')
    
    if not os.path.exists(log_file):
        yield "data: Log file not found. Waiting for process to start...\n\n"
        await asyncio.sleep(2)
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                yield f"data: {line.strip()}\n\n"
            
            while True:
                line = f.readline()
                if not line:
                    try:
                        with open(status_file, 'r') as sf:
                            status_data = json.load(sf)
                            if status_data.get("status") in ["completed", "failed"]:
                                break 
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass 
                    await asyncio.sleep(1)
                    continue
                yield f"data: {line.strip()}\n\n"
    except asyncio.CancelledError:
        print(f"Log stream was cancelled by client for user {user_id}.")
    finally:
        print(f"Log stream is closing for user {user_id}.")
        yield "event: close\ndata: The build process has finished or the stream has been disconnected.\n\n"

@router.get("/build/{user_id}/status", response_model=Dict)
def get_build_status(
    user_id: int,
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    """[ADMIN] Checks the build status for a user."""
    status_file = os.path.join(DATASETS_DIR, str(user_id), 'build_status.json')
    if not os.path.exists(status_file):
        return {"status": "not_started"}
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"status": "unknown"}
        
@router.get("/build/{user_id}/config", response_model=Dict)
def get_model_config(
    user_id: int,
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    """[ADMIN] Gets the model build config for a user."""
    user_config_file = os.path.join(DATASETS_DIR, str(user_id), 'model_config.json')
    
    if os.path.exists(user_config_file):
        try:
            with open(user_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config_data)
                return merged_config
        except Exception as e:
            print(f"Error reading user config for {user_id}: {e}")
            return DEFAULT_CONFIG
            
    return DEFAULT_CONFIG

@router.post("/build/{user_id}/config", status_code=status.HTTP_200_OK)
async def save_model_config(
    user_id: int,
    request: Request, 
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    """[ADMIN] Saves or updates the 'model_config.json' for a user."""
    user_output_dir = os.path.join(DATASETS_DIR, str(user_id))
    os.makedirs(user_output_dir, exist_ok=True)
    user_config_file = os.path.join(user_output_dir, 'model_config.json')

    try:
        config_data = await request.json()
        if not isinstance(config_data, dict):
            raise HTTPException(status_code=400, detail="Request body must be a valid JSON object.")
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Error processing request: {e}")

    try:
        user_overrides = {}
        for key, value in config_data.items():
            if key in DEFAULT_CONFIG:
                if DEFAULT_CONFIG[key] != value:
                    user_overrides[key] = value
            else:
                user_overrides[key] = value

        with open(user_config_file, 'w', encoding='utf-8') as f:
            json.dump(user_overrides, f, indent=2)
        
        return {"message": "Model parameters saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config file to server: {e}")


@router.post("/build/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def start_build_for_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    build_mode: str = "resume", 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin_user)
):
    """[ADMIN] Triggers the model building pipeline for a user."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_admin == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student user not found.")

    if build_processes.get(user_id):
        raise HTTPException(status_code=409, detail=f"A build process is already running for user {user_id}.")

    user_output_dir = os.path.join(DATASETS_DIR, str(user_id))
    os.makedirs(user_output_dir, exist_ok=True)
    
    logger = setup_user_logger(user_id)
    
    if build_mode == "rebuild_full":
        if os.path.exists(os.path.join(user_output_dir, 'build.log')):
            os.remove(os.path.join(user_output_dir, 'build.log'))
        if os.path.exists(os.path.join(user_output_dir, 'build_status.json')):
            os.remove(os.path.join(user_output_dir, 'build_status.json'))
        
        logger.info("INFO: 'Full Rebuild' mode. Clearing all existing .json model files...")
        try:
            for f in os.listdir(user_output_dir):
                if f.endswith('.json') and f not in ['model_config.json', 'evaluation_status.json', 'evaluation_results.json', 'evaluation_testset.json']:
                    os.remove(os.path.join(user_output_dir, f))
        except Exception as e:
            logger.error(f"ERROR: Failed to clear old files (full): {e}")
            
    elif build_mode == "rebuild_l1_up":
        if os.path.exists(os.path.join(user_output_dir, 'build_status.json')):
            os.remove(os.path.join(user_output_dir, 'build_status.json'))

        logger.info("INFO: 'Rebuild L1-L(n)' mode. Clearing L1 and higher .json files...")
        try:
            for f in os.listdir(user_output_dir):
                if f.endswith('.json') and not f.startswith('L0_') and f not in ['model_config.json', 'evaluation_status.json', 'evaluation_results.json', 'evaluation_testset.json']:
                    os.remove(os.path.join(user_output_dir, f))
        except Exception as e:
            logger.error(f"ERROR: Failed to clear old files (L1+): {e}")

    elif build_mode == "rebuild_l2_up":
        if os.path.exists(os.path.join(user_output_dir, 'build_status.json')):
            os.remove(os.path.join(user_output_dir, 'build_status.json'))

        logger.info("INFO: 'Rebuild L2-L(n)' mode. Clearing L2 and higher .json files...")
        try:
            for f in os.listdir(user_output_dir):
                if f.endswith('.json') and f.startswith('L') and len(f) > 1 and f[1].isdigit():
                    layer_num = int(f[1])
                    if layer_num >= 2:
                        os.remove(os.path.join(user_output_dir, f))
                        logger.info(f"INFO: Deleted old file: {f}")
        except Exception as e:
            logger.error(f"ERROR: Failed to clear old files (L2+): {e}")

    build_processes[user_id] = True
    background_tasks.add_task(run_model_pipeline_for_user, user_id, build_mode)
    return {"message": "Model build process started."}

@router.get("/build/{user_id}/stream")
async def stream_build_logs(
    user_id: int,
    request: Request,
    current_admin: models.User = Depends(security.get_current_admin_user_from_query)
):
    """[ADMIN] Streams logs from the build process for a user via SSE."""
    return StreamingResponse(log_streamer(user_id), media_type="text/event-stream")





# --- OTHER ENDPOINTS ---

@router.get("/users", response_model=List[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db), current_admin: models.User = Depends(security.get_current_admin_user)):
    """[ADMIN] Retrieves a list of all non-admin users."""
    return db.query(models.User).filter(models.User.is_admin == False).all()

@router.get("/datasets", response_model=List[Dict[str, str]]) 
def get_available_datasets(
    db: Session = Depends(get_db)
):
    """[ADMIN] Lists the user IDs and names for which a model has been successfully built."""
    dataset_ids = []
    try:
        if not os.path.exists(DATASETS_DIR): 
            return []
        dataset_ids = [int(d) for d in os.listdir(DATASETS_DIR) if os.path.isdir(os.path.join(DATASETS_DIR, d)) and d.isdigit()]
    except FileNotFoundError: 
        return []
    
    if not dataset_ids:
        return []
        
    users = db.query(models.User.id, models.User.realname, models.User.student_id).filter(models.User.id.in_(dataset_ids)).all()
    
    user_data = []
    for user in users:
        username = user.realname or user.student_id or f"User {user.id}"
        user_data.append({"id": str(user.id), "username": username})
    
    return sorted(user_data, key=lambda x: x['username'])

@router.get("/graph-data")
def get_graph_data_for_dataset(dataset: str):
    """[ADMIN] Retrieves the consolidated graph data for a given user dataset."""
    dataset_path = os.path.join(DATASETS_DIR, dataset)
    if not os.path.isdir(dataset_path):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' not found.")
    all_nodes, links, dimensions = [], [], {}
    try:
        instance_file = os.path.join(dataset_path, 'L0_keyinfo_instances.json')
        if os.path.exists(instance_file):
            with open(instance_file, 'r', encoding='utf-8') as f:
                for inst in json.load(f):
                    content_parts = []
                    when_info = inst.get('WHEN', {})
                    when_str = when_info.get('time_range') or when_info.get('time_of_day')
                    if when_str:
                        content_parts.append(f"When: {when_str}")
                    if where := inst.get('WHERE'): content_parts.append(f"Where: {where}")
                    if who := inst.get('WHO'): content_parts.append(f"Who: {who}")
                    if why := inst.get('WHY'): content_parts.append(f"Why: {why}")
                    if how := inst.get('HOW'): content_parts.append(f"How: {how}")
                    content = "\n".join(content_parts)

                    all_nodes.append({
                        "id": inst['idx'], 
                        "node_id": inst['idx'], 
                        "layer": 0, 
                        "title": inst.get('WHAT', 'Instance'), 
                        "content": content,
                        "model_type": "Shared" # L0 is shared
                    })

        for file in sorted(os.listdir(dataset_path)):
            path = os.path.join(dataset_path, file)
            if file.endswith('_nodes.json'):
                with open(path, 'r', encoding='utf-8') as f: 
                    nodes_list = json.load(f)
                    # Determine model type based on filename
                    is_hl = "HL_" in file
                    for n in nodes_list:
                        n['model_type'] = "HL" if is_hl else "Standard"
                    all_nodes.extend(nodes_list)
            elif file.endswith('_dimensions.json'):
                if match := re.search(r'L(\d+)_', file):
                    with open(path, 'r', encoding='utf-8') as f: dimensions[match.group(1)] = json.load(f)
        for node in all_nodes:
            if target_id := (node.get('node_id') or node.get('id')):
                for source_id in node.get('source_nodes', []) + node.get('source_instances', []):
                    links.append({"source": source_id, "target": target_id})
        return {"nodes": all_nodes, "links": links, "dimensions": dimensions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing graph data: {e}")