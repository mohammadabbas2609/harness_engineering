"""
Git tools: this wraps commit/diff/logs/checkout/branch op as a harness tools

All operations run within a workspace as the working directory pinned by code not supplied by model. workspace is auto-initiliazed by git so model dont have to do 'git init'
"""


import subprocess
from harness.tools.registry import tool
from harness.tools.filesystem import WORKSPACE


# Since we'll only use git for locall version control, it should be pretty quick, if command invocation tooks more than given time in GIT_TIMEOUT (in seconds) we'll kill that process

GIT_TIMEOUT = 10 

def _run_git(*args: str) -> str:
  """
    Run a git command and return result combined output string
    First arg is hardcoded in WORKSPACE so it didnt get influenced by model, non zero exit code (failure) are not raised output is returned with exit code so model and view it and decide it's next steps
  """

  command_output = subprocess.run(
    ["git", *args],
    cwd=WORKSPACE,
    capture_output=True,
    text=True,
    timeout=GIT_TIMEOUT,
    check=False #dont raise non zero exit, model handles the error
  )

  output = command_output.stdout.strip() or command_output.stderr.strip()

  if command_output.returncode != 0:
    return f"[git exit with code {command_output.returncode} {output}]"

  return output or "(no output)"



if not (WORKSPACE / ".git").exists():
  #Initializing git along with other parameters
  _run_git("init")
  _run_git("config", "user.name", "agent")
  _run_git("config", "user.email", "example@gmail.com")
  _run_git("symbolic-ref", "HEAD", "refs/heads/master")


@tool
def git_status() -> str:
  """Shows the status of workspace, added, modified, staged untracked files"""
  return _run_git("status", "--short")

@tool
def git_diff(path: str = "") -> str:
  "Shows unstaged changes in workspace. Optionally restrict to a single path"
  args = ["diff"]
  if path:
    args.append(path)
  return _run_git(*args)


@tool
def git_log(limit: int = 10) -> str:
  """Shows recent commit history, default to last 10 commits"""
  return _run_git("log", f"-n {limit}", "--oneline")


@tool
def git_commit(message: str = "") -> str:
  """Stage all current changes and commit them with a message, 
    returns the hash of the commit or error stating 'nothing to commit'
  """

  if not len(message):
    return "please provide commit message"
  
  _run_git("add", ".")

  return _run_git("commit", "-m", message)


@tool
def git_checkout(ref: str) -> str:
  """Switch to commit or branch rollback(to earlier commit) and branch switching(to a sibling branch)"""
  return _run_git("checkout", ref)

@tool
def git_branch(name: str) -> str:
  """List brances if called with no arg. create a new branch if arg is provided, does not switch to a new branhc use git_checkout to checkout to that branch after creating one from this"""

  if not len(name):
    return _run_git("branch")

  return _run_git("branch", name)

@tool
def git_merge(branch: str, message: str = "") -> str:
  """
  Merge the specified branch into the currently checked-out branch.

  Args:
    branch: Branch or commit to merge into the current branch.
    message: Optional custom merge commit message.

  Returns:
    Git merge output, including conflicts or errors.
  """

  if not len(branch):
    return "please provide branch name"

  args = ["merge"]

  if message:
    args.extend(["-m", message])

  args.append(branch)

  return _run_git(*args)