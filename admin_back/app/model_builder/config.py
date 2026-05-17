# This config is specific to the model building pipeline.
# It's kept separate from the main app's config.

import os

# --- Path Configuration ---
OUTPUT_DIR = "app/static/datasets"


# --- Pipeline Control ---
TOTAL_LAYERS = 4 


# --- LLM & API Configuration ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_MAX_RETRIES = 2
API_RETRY_DELAY = 4  
API_REQUEST_DELAY = 4 
MAX_OUTPUT_TOKENS = 32768 


# --- Clustering Configuration ---
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# --- Initial Clustering (Step 2) ---
UMAP_N_COMPONENTS = 25
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
HDBSCAN_MIN_CLUSTER_SIZE = 3 

# --- Recursive Re-clustering (Step 3) ---
MAX_CLUSTER_SIZE = 70
KMEANS_SPLIT_FACTOR = 30

# --- Validation Rules (Step 5) ---
FINAL_MIN_RECURRENCE = 2 
FINAL_MIN_CLUSTER_SIZE = 2 


# --- Higher-Layer Synthesis Configuration ---
DIMENSION_SAMPLE_SIZE = 30 
NUM_DIMENSIONS_PER_LAYER = 3 

# --- NEW: Cluster Count Control ---
# 0 = Auto (Heuristic)
TARGET_CLUSTERS_PER_DIMENSION = 0
# Per-Layer Overrides
TARGET_CLUSTERS_BY_LAYER = {
    "L2": 4,
    "L3": 3,
    "L4": 2
}

# --- Model Update/Alignment Configuration ---
SIMILARITY_THRESHOLD = 0.67