import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
import logging

from .data_structures import KnowledgeNode
from . import llm_handler, config

# --- CONFIGURATION ---
MODEL_NAME = config.EMBEDDING_MODEL

# --- PROMPTS ---

AUGMENTATION_DECISION_PROMPT = """
You are a Knowledge Graph Architect. Your task is to maintain the accuracy of a user's "Thinking Model" by processing a new "Ground Truth" QA pair.

INPUTS:
1. **Ground Truth**: A Q&A pair derived from the user's latest feedback. This is the absolute truth.
   - Question: "{question}"
   - Answer: "{answer}"

2. **Relevant Context Nodes**: Existing nodes in the model that are semantically similar to this topic.
{context_nodes_text}

TASK:
Analyze the Ground Truth against the Context Nodes. Determine the single best action to take.

ACTIONS:
- **KEEP**: The information in the QA pair is already fully and accurately represented in the Context Nodes. No changes needed.
- **MODIFY**: The QA pair contradicts a specific node OR provides specific details that refine a vague concept in a specific node. (You must provide the *complete* new content for that node).
- **DELETE**: The QA pair proves a specific node is factually wrong, hallucinated, or obsolete.
- **ADD**: The QA pair introduces a *new* concept or habit not covered by any existing node. (Only use ADD if it cannot be merged into an existing node via MODIFY).

RULES:
- If MODIFY or DELETE, you MUST specify the `target_node_id` from the provided list.
- If ADD, `target_node_id` should be null.
- If MODIFY or ADD, you MUST provide `new_content`.
- `new_content` must be a concise, comprehensive statement (third-person perspective, e.g., "The user believes...").

OUTPUT SCHEMA (JSON):
{{
  "action": "KEEP" | "MODIFY" | "DELETE" | "ADD",
  "target_node_id": "string (The ID of the node to modify/delete, or null for ADD/KEEP)",
  "reasoning": "string (Why you chose this action)",
  "new_content": "string (The full text of the new or updated node content)"
}}
"""

class AugmentationEngine:
    def __init__(self, user_id: int, all_nodes: List[KnowledgeNode]):
        self.user_id = user_id
        self.nodes = all_nodes
        self.node_map = {n.node_id: n for n in all_nodes}
        self.embedding_model = None
        self.embeddings = None
        self.node_ids_list = [] # Keeps track of row-index to node-id mapping for embeddings
        
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Loads model and computes initial embeddings."""
        print(f"  [Engine] Loading embedding model '{MODEL_NAME}'...")
        try:
            self.embedding_model = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            print(f"  [Engine] Error loading embedding model: {e}")
            return

        self._refresh_embeddings()

    def _refresh_embeddings(self):
        """Re-computes embeddings for the current state of nodes."""
        if not self.nodes:
            self.embeddings = np.array([])
            self.node_ids_list = []
            return

        print(f"  [Engine] Refreshing embeddings for {len(self.nodes)} nodes...")
        contents = [f"{n.title}: {n.content}" for n in self.nodes]
        self.node_ids_list = [n.node_id for n in self.nodes]
        self.embeddings = self.embedding_model.encode(contents, convert_to_tensor=True)

    def find_relevant_nodes(self, query: str, top_k: int = 5) -> List[KnowledgeNode]:
        """Uses RAG to find nodes most similar to the query."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        
        # Compute cosine similarity
        cos_scores = util.cos_sim(query_embedding, self.embeddings)[0]
        
        # Get top_k results
        top_results = list(reversed(sorted(zip(cos_scores, range(len(cos_scores))))))[:top_k]
        
        relevant_nodes = []
        for score, idx in top_results:
            node_id = self.node_ids_list[int(idx)]
            relevant_nodes.append(self.node_map[node_id])
            
        return relevant_nodes

    def process_batch(self, qa_dataset: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Processes a full batch of QA pairs.
        Returns stats on actions taken.
        """
        stats = {"KEEP": 0, "MODIFY": 0, "DELETE": 0, "ADD": 0}
        
        print(f"\n[Engine] Starting processing of {len(qa_dataset)} QA pairs...")

        for i, qa_pair in enumerate(qa_dataset):
            question = qa_pair.get("question", "")
            answer = qa_pair.get("answer", "")
            query = f"{question} {answer}"

            # 1. RAG Retrieval
            relevant_nodes = self.find_relevant_nodes(query, top_k=5)
            
            # Format nodes for prompt
            context_nodes_text = ""
            for node in relevant_nodes:
                context_nodes_text += f"- [ID: {node.node_id}] {node.title}: {node.content}\n"

            if not context_nodes_text:
                context_nodes_text = "(No existing nodes found. Model is empty.)"

            # 2. LLM Decision
            prompt = AUGMENTATION_DECISION_PROMPT.format(
                question=question,
                answer=answer,
                context_nodes_text=context_nodes_text
            )
            
            try:
                time.sleep(3) # Rate limit safety
                response = llm_handler.query_api_with_retries(
                    prompt=prompt,
                    model=llm_handler.MODEL_LITE,
                    outjson=True
                )
                
                if not response or not isinstance(response, dict):
                    print(f"  [Step {i+1}] Invalid LLM response. Skipping.")
                    continue
                
                action = response.get("action", "KEEP").upper()
                target_id = response.get("target_node_id")
                new_content = response.get("new_content")
                reasoning = response.get("reasoning", "")
                
                print(f"  [Step {i+1}] Action: {action} | Target: {target_id} | Reason: {reasoning}")
                
                # 3. Apply Action
                self._apply_action(action, target_id, new_content, qa_pair, reasoning)
                stats[action] += 1

            except Exception as e:
                print(f"  [Step {i+1}] Error: {e}")

        # Final refresh to ensure everything is consistent if we were doing granular updates
        # (Though we updated in-memory lists during _apply_action)
        return stats

    def _apply_action(self, action, target_id, new_content, qa_pair, reasoning):
        """Applies the decision to the in-memory graph state."""
        
        if action == "KEEP":
            return

        if action == "MODIFY":
            if target_id in self.node_map and new_content:
                node = self.node_map[target_id]
                node.content = new_content
                # Update embedding for this specific node (optimization: do simpler list refresh for now)
                # For robust batching without complex index management, we update the map/list
                # but we usually wait for batch end to re-index unless we really need iterative context.
                # Here we will NOT re-index every step for speed, assuming batch QA doesn't conflict heavily.
            else:
                print(f"    [Warn] MODIFY failed: Target {target_id} not found or no content.")

        elif action == "DELETE":
            if target_id in self.node_map:
                # Remove from map
                del self.node_map[target_id]
                # Remove from list
                self.nodes = [n for n in self.nodes if n.node_id != target_id]
            else:
                print(f"    [Warn] DELETE failed: Target {target_id} not found.")

        elif action == "ADD":
            if new_content:
                # Infer layer from source if possible, else default to L1
                source_id_hint = qa_pair.get("source_node_id", "")
                layer = 1
                if "L2" in source_id_hint: layer = 2
                elif "L3" in source_id_hint: layer = 3
                elif "L4" in source_id_hint: layer = 4
                
                new_id = f"L{layer}_AUG_{int(time.time())}_{len(self.nodes)}"
                new_node = KnowledgeNode(
                    node_id=new_id,
                    layer=layer,
                    title=f"Augmented Insight ({qa_pair.get('question_type', 'General')})",
                    content=new_content,
                    source_instances=[], # Can't link to raw text easily here
                    source_nodes=[]
                )
                self.nodes.append(new_node)
                self.node_map[new_id] = new_node
                print(f"    > Added new node: {new_id}")

    def get_updated_layers(self) -> Dict[int, List[KnowledgeNode]]:
        """Separates the monolithic node list back into layers."""
        layers = {1: [], 2: [], 3: [], 4: []}
        for node in self.nodes:
            if node.layer in layers:
                layers[node.layer].append(node)
        return layers