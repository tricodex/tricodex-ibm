Watson supported models: ['codellama/codellama-34b-instruct-hf', 
'google/flan-t5-xl', 'google/flan-t5-xxl', 'google/flan-ul2', 
'ibm/granite-13b-instruct-v2', 'ibm/granite-20b-code-instruct', 
'ibm/granite-20b-multilingual', 'ibm/granite-3-2-8b-instruct-preview-rc', 
'ibm/granite-3-2b-instruct', 'ibm/granite-3-8b-instruct', 
'ibm/granite-34b-code-instruct', 'ibm/granite-3b-code-instruct', 
'ibm/granite-8b-code-instruct', 'ibm/granite-guardian-3-2b', 
'ibm/granite-guardian-3-8b', 'meta-llama/llama-2-13b-chat', 
'meta-llama/llama-3-1-70b-instruct', 'meta-llama/llama-3-1-8b-instruct', 
'meta-llama/llama-3-2-11b-vision-instruct', 
'meta-llama/llama-3-2-1b-instruct', 'meta-llama/llama-3-2-3b-instruct', 
'meta-llama/llama-3-2-90b-vision-instruct', 
'meta-llama/llama-3-3-70b-instruct', 'meta-llama/llama-3-405b-instruct', 
'meta-llama/llama-guard-3-11b-vision', 'mistralai/mistral-large', 
'mistralai/mixtral-8x7b-instruct-v01']

Going to use novel RAR framework:

RAR (Retrieval-Augmented Reasoning) is an advancement beyond traditional RAG (Retrieval-Augmented Generation). While RAG simply retrieves relevant information to augment prompts, RAR adds a layer of reasoning:

Information Retrieval: Like RAG, it retrieves relevant information from a knowledge base
Reasoning Layer: Unlike RAG, it then:

Analyzes relationships between retrieved information
Forms logical chains of reasoning
Makes deductions and inferences
Validates conclusions
Creates new knowledge connections

Multi-Agent Coordination: Often involves multiple specialized agents that:

Perform different types of reasoning
Work with different tools
Coordinate to solve complex problems

https://arxiv.org/pdf/2502.04644