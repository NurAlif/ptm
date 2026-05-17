# This file is copied directly from your 'aplication to be refactored.txt'
# It contains all the prompt templates for the LLM.

KEY_INFO_EXTRACTION = """
You are an AI assistant that analyzes personal narratives to extract and categorize unique key information about the user food and study. When given a text where "I" represents the user, identify and classify information that falls into these categories:

1. Decisions/Choices: Conscious choices between alternatives
2. Activity: Things the user did or steps they took
3. Reactions: Emotional or physical responses to situations
4. Problem and Problem-solving approaches of user

Then, describe an instance of all above using 5W1H:
1. WHAT: the main decision, activity, reaction, or problem/problem solving
2. WHEN: Time of the instance above, mention the time in what day and hour in xx:xx-yy:yy format (eg. Friday, 10:00-12:30), if the hour time duration is only the start then output xx:xx, then output the duration in hour.
3. WHERE: The detailed place of the instance above,
4. WHO: Anyone involved in the instance except user. if only user than return ""
5. WHY: The reason of instance, the consideration betwen choices, or motivation
6. HOW: The method or process 

WHAT, WHEN, WHERE is mandatory, else is optional.

Assign an indexed id of each instances arrange it in chronological order.

Output the extracted information using this JSON schema:
Info = {{"type": str, "WHAT":str, "WHEN":str, "WHERE": str, "WHO": str, "WHY":str, "HOW":str}}
Return = {{
    "informations": Array<Info>
}}

Guidelines:
- Use thirdperson-person perspective using "User" pronoun to refer to user when describing the content
- Include relevant context when necessary for clarity
- Each entry 5W1H should be a complete comprehensive, standalone piece of information
- Avoid redundant or overlapping entries
- Informations items must be significantly unique!
- Preserve the user's accurate original meaning and intent
- Don't lose information from the source text.
- If 5W1H information does not exist or unknown, then don't output that 5W1H item object property. Don't say "unspecified" or "unknown". just exclude the property!
- If 5W1H item information is not explicitly mentioned but obviously known, you can answer the by guest but you should prefer to fill with the bigger/wide scope of the location or time or information. dont say implied if you know it implicitly. just output clean output.

Input text:
{text}
"""

ACCURATE_TIME_FORMATTING = """
You are a time-formatting AI. Given a natural language string describing a time, convert it into a structured JSON object.

The output must be a single, valid JSON object with the following schema. Do not include any other text or markdown formatting.
{{
  "weekday": "string (e.g., Monday, Sunday) or empty",
  "time_of_day": "string (e.g., morning, afternoon, evening, night) or empty",
  "time_range": "string (e.g., 10:00-12:30) or empty",
  "duration_hours": "float or empty"
}}

TIME INPUT:
{time_string}
"""

ACCURATE_TIME_FORMATTING_BATCH = """
You are an time-formatting AI. Given a JSON object containing multiple natural language time descriptions, convert each one into a structured JSON object.

RULES:
- Process each time string independently based on its key.
- The output MUST be a single, valid JSON object where each key corresponds to an input key, and the value is the structured time object.
- Do not include any other text or markdown formatting.

OUTPUT SCHEMA for each entry:
{{
  "weekday": "string (e.g., Monday, Sunday) or empty",
  "time_of_day": "string (e.g., morning, afternoon, evening, night) or empty",
  "time_range": "string (e.g., 10:00-12:30) or empty",
  "duration_hours": "float or empty"
}}

INPUT JSON:
{time_strings_json}
"""

TOPIC_CLASSIFICATION_PROMPT = """
You are a text classification AI. Your task is to analyze a list of user activities
and provide a single, concise topic category for the entire group.

Categories should be 1-2 words, such as "Study", "Social Activity", "Food", 
"Religious Activity", "Personal Care", "Stock Trading", "Entertainment", or "Other".

Analyze the following instances and return ONLY the single most appropriate category name.
Do not add any other text, just the category.

INSTANCES:
{instances_text}
"""

DIRECT_INFERENCE_GENERATION = """
You are a behavioral analyst AI. Analyze the following cluster of user activities and synthesize the core, recurring behavioral pattern(s) they represent. A single cluster can sometimes contain more than one distinct pattern.

Your task is to generate **one to three (1-3)** distinct patterns from this cluster.

RULES:
- Your entire output MUST be a single, valid JSON **array** of pattern objects.
- **Only** generate more than one pattern if the activities clearly show separate, non-overlapping behaviors. For example, 'Morning Academic Routine' and 'Afternoon Socializing' are two distinct patterns, but 'Studying for Exam' and 'Doing Homework' should be combined into one 'Academic Work' pattern.
- If all activities are very similar, just generate **one** pattern. Do not force multiple patterns if one is sufficient.
- Each pattern object in the array must contain:
  1. `title`: A concise, descriptive title for the pattern (3-7 words).
  2. `content`: A comprehensive paragraph describing the pattern.
  3. `source_instances`: A JSON array of the original instance IDs that support *this specific pattern*.
- Refer to the subject as "The user".
- Do not include markdown formatting or any other text in your response.
- Do not mention source_instances in the content, instead just make sure it is included in the "source_instances" output property.
- The content and the title of the inference must be easy to understand and utilize well known vocabularies. dont use difficult vocabularies!

OUTPUT SCHEMA (A JSON Array):
[
  {{
    "title": "string",
    "content": "string",
    "source_instances": ["string (instance_id)", ...]
  }}
]

SOURCE INSTANCE IDs (from the cluster):
{instance_ids_json}

CLUSTERED INSTANCES (for analysis):
{instances_text}
"""

DIMENSION_GENERATION = """
You are a cognitive science expert. Your task is to analyze a sample of a user's foundational behavioral patterns (Layer {layer_number}) and devise a complete, hierarchical set of analytical dimensions for all higher layers (Layer 2, 3, and 4) at once.

You must follow this precise hierarchical structure:

- **Layer 2 Dimensions (Low-Level Abstraction):**
  - **Focus:** Fundamental **behavioral patterns, habits, routines, and immediate triggers**.
  - **Keywords:** "Routine", "Habit", "Behavior Pattern", "Schedule", "Trigger".
  - **Example Titles:** "Routine Analysis", "Habit Formation", "Schedule Adherence Patterns", "Trigger-Response Analysis".

- **Layer 3 Dimensions (Medium-Level Abstraction):**
  - **Focus:** The user's **reasoning, plans, priorities, goals, and targets**.
  - **Keywords:** "Goal", "Target", "Plan", "Reasoning", "Priority".
  - **Example Titles:** "Goal-Setting Strategies", "Task Prioritization Logic", "Planning vs. Reactivity", "Reasoning Models".

- **Layer 4 Dimensions (High-Level Abstraction):**
  - **Focus:** The user's **core values, deep motivations, strategic thinking, and complex problem-solving models**.
  - **Keywords:** "Core Values", "Motivation", "Problem Solving", "Strategic Thinking", "Beliefs".
  - **Example Titles:** "Core Value Identification", "Motivational Drivers", "Problem-Solving Frameworks", "Strategic Thinking Patterns".

INSTRUCTIONS:
1.  Analyze the provided Layer {layer_number} patterns (which are Layer 1 patterns).
2.  Generate exactly {num_dimensions} dimensions for EACH of the three layers (L2, L3, L4).
3.  Each dimension must have a `title` and a `description`.
4.  **CRITICAL:** The `title` of each dimension should be **general** and directly reflect its layer's focus, incorporating keywords from that layer (e.g., 'Habit Analysis', 'Goal Prioritization', 'Core Value Identification'). The `description` should then explain how this general lens applies to the user's specific patterns.
5.  The output MUST be a single, valid JSON object with keys "L2", "L3", and "L4".
6.  Do not include markdown formatting or any other text.
7. The content and title sould be clear. Must use easy words! dont use difficult vocabulary! just use easy to read and understand common vocabularies!

OUTPUT SCHEMA:
{{
  "L2": [
    {{ "title": "string", "description": "string" }},
    {{ "title": "string", "description": "string" }}
  ],
  "L3": [
    {{ "title": "string", "description": "string" }},
    {{ "title": "string", "description": "string" }}
  ],
  "L4": [
    {{ "title": "string", "description": "string" }},
    {{ "title": "string", "description": "string" }}
  ]
}}

SAMPLE LAYER {layer_number} PATTERNS:
{sampled_nodes_text}
"""

NODE_REFINEMENT = """
You are an AI model maintainer. Your task is to update and refine an existing behavioral pattern based on a new set of related observations.

Combine the insights from the new observations with the existing pattern to create a more accurate, comprehensive, and nuanced description. Output only the updated `content`.

RULES:
- The new description should seamlessly integrate the old and new information.
- Do not lose any critical information from the original pattern.
- The output must be a single JSON object. Do not include markdown formatting or any other text.
- The content must be described using clear and easy to understand vocabularies! dont use difficult vocabularies for the content! It must be straight forward sentence!

OUTPUT SCHEMA:
{{
  "updated_content": "string"
}}

EXISTING BEHAVIORAL PATTERN:
{existing_node_content}

NEW RELATED OBSERVATIONS:
{new_instances_text}
"""


PROMPT_RAG_ANSWER_FROM_CONTEXT = """
You are an dataset maker. Answer the user's query based *only* on the provided "Knowledge Context".
Do not use any prior knowledge. If the context does not contain the answer, state that the information is not available.

DONT USE SAME WORDING!
- Use different wording compared with the stated knowledge context!
- Use different way to tell the answer compared with stated knowledge context!
- Dont reference to knowledge context!
- Tell the answer like you know it by yourself, not by the knowledge context!

Keep the answer concise and to the point but include the reasoning. The reasoning must be well known made up reasoning or logical reason, dont refer to real reasoning from knowledge context!

QUERY:
{query}

KNOWLEDGE CONTEXT:
{context}

CONCISE ANSWER:
"""


SELECT_RELEVANT_NODES = """
You are an AI research assistant. Your task is to analyze a list of numbered "Source Nodes" (from Layer 1) and determine which ones are relevant for synthesizing a new insight based on a given "Analytical Dimension" (for Layer 2).

ANALYTICAL DIMENSION:
- Title: {dimension_title}
- Description: {dimension_description}

RULES:
1.  Read the dimension carefully. This is the *only* lens you should use.
2.  Read the numbered list of "Source Nodes" below.
3.  Identify all nodes that provide direct evidence, examples, or context related to the analytical dimension.
4.  Your output MUST be a single, valid JSON object with one key: "relevant_node_indices".
5.  The value for this key must be a JSON list of the *numbers* (as integers) of the relevant nodes.
6.  If no nodes are relevant, return an empty list.

EXAMPLE RESPONSE:
{{
  "relevant_node_indices": [2, 5, 14]
}}

NUMBERED SOURCE NODES:
{numbered_nodes_text}
"""

# --- NEW: Dimensional Clustering Prompt ---
DIMENSIONAL_CLUSTERING_PROMPT = """
You are a pattern recognition engine. Your goal is to group a list of behavioral nodes into distinct clusters based SPECIFICALLY on the provided "Analytical Dimension".

ANALYTICAL DIMENSION (The Lens):
- Title: {dimension_title}
- Description: {dimension_description}

INSTRUCTIONS:
1. Read the list of "Source Nodes" below.
2. Group these nodes into {num_clusters} distinct clusters based on how they relate to the Analytical Dimension.
3. Every node in a cluster must share a specific commonality regarding the dimension (e.g., if the dimension is "Triggers", Cluster A might be "Social Triggers", Cluster B might be "Academic Triggers").
4. Ensure every cluster has at least 2 nodes.
5. A node can belong to multiple clusters if it fits, but try to be distinct.

OUTPUT SCHEMA:
Returns a JSON Object containing a list of clusters.
{{
  "clusters": [
    {{
      "cluster_label": "string (Short descriptive label for this group)",
      "node_indices": [1, 5, 8] (The ID numbers of the nodes in this cluster)
    }},
    ...
  ]
}}

SOURCE NODES:
{numbered_nodes_text}
"""

# --- MODIFIED: Synthesis Prompt (Now supports MULTIPLE insights per cluster) ---
GRAPH_BASED_SYNTHESIS = """
You are a behavioral analyst.
Your task is to synthesize high-level cognitive insights from a specific CLUSTER of user patterns, viewed through a specific Dimension.

ANALYTICAL DIMENSION:
- Title: {dimension_title}
- Description: {dimension_description}

CLUSTER LABEL: {cluster_label}

INSTRUCTIONS:
1. Analyze the provided "Cluster Patterns".
2. Synthesize **1 to 3** distinct, profound insights that explain *why* these patterns exist together under this dimension.
3. If the patterns are complex, split them into distinct insights. If they are simple, one insight is sufficient.
4. Each insight should be abstract and model-level (e.g., "The user relies on external structure to mitigate anxiety" rather than just "The user uses a calendar").
5. The content and title sould be clear. Must use easy words! dont use difficult vocabulary! just use easy to read and understand vocabularies!

OUTPUT SCHEMA:
Returns a JSON **Array** of insight objects.
[
  {{
    "title": "string (3-7 words, abstract and professional)",
    "content": "string (Comprehensive paragraph explaining the insight)",
    "source_nodes": ["string (node_id)", ...]
  }}
]

CLUSTER PATTERNS (INPUT):
{source_nodes_json}
"""