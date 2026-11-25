
# Model

MODEL: str = "gpt-5-mini"

COMPACTION_MODEL: str = "gpt-5-mini"

# MODEL: str = "gpt-5-mini"


# ReAct loop bounds ---
# The amount of tool call per user turn the model can do, when hit the harness forces the model to summarize what it did and hand back the control to user instead of running loop infinitely

STEP_BUDGET: int = 25



# --- Tools Timeout (seconds) ---
# After particular duration we kill the command so it dont stay forever when stucked

GIT_TIMEOUT: int = 10

BASH_TIMEOUT: int = 60


# Command Alllow List

ALLOW_LIST: set[str] = { 
  "python", "python3", "pip" , "pip3",
  
  "ls", "cat", "grep", "wc", "head", "tail", "find",
  
  "which", "echo", "pwd", "git" 
}


# Command Deny List, if the command is in deny list it will not be performed, doesnt matter if it's in even allow list, somethin like IAM policy

DENY_LIST: set[str] =  { "dd", "sudo", "mkfs", "mv" }



# -------- SANDBOX CONFIGURATION -----------------

SANDBOX_IMAGE: str = "agent-harness:0.1"

SANDBOX_WORKSPACE_PATH:str = "/workspace"

SANDBOX_STARTUP_TIMEOUT :int = 30

SANDBOX_CONTAINER_PREFIX: str = "idk-container-"


# Controlling the number of result that is returned by web search, 5 seems fine for enough context and not to bloat context much
WEBSEARCH_MAX_RESULT: int = 5

# -- RAG memory --    
# Path to the knowledge corpus (documents to be indexed and retrieved
# from). Lives at project root, not in workspace, so it survives
# workspace clean-slates.
RAG_CORPUS_PATH: str = "knowledge"

# Path to ChromaDB's persistent storage. Also at project root; gitignored
# because it's derived from the corpus and regenerable in seconds.
RAG_INDEX_PATH: str = ".rag_index"

# OpenAI's embedding model. text-embedding-3-small is cheap
# (~$0.02 per 1M tokens) and good enough for most retrieval tasks.
RAG_EMBEDDING_MODEL: str = "text-embedding-3-small"

# Target chunk size in tokens (approximate). Balances retrieval precision
# (smaller = more precise hits) against context per hit (larger = more
# useful passages).
RAG_CHUNK_SIZE: int = 500

# Overlap between adjacent chunks, in tokens. Smooths the case where
# relevant content straddles a chunk boundary.
RAG_CHUNK_OVERLAP: int = 50

# Default number of results the recall tool returns. The model can
# override this via max_results.
RAG_DEFAULT_RESULTS: int = 5