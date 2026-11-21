
# Model

MODEL: str = "gpt-4o-mini"


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

SANDBOX_IMAGE: str = "python:3.11-slim"

SANDBOX_WORKSPACE_PATH:str = "/workspace"

SANDBOX_STARTUP_TIMEOUT :int = 30

SANDBOX_CONTAINER_PREFIX: str = "idk-container-"