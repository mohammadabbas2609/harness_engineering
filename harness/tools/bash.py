"""Bash tool: A meta tool that will be used to execute bash command by giving agent access to shell"""

import subprocess
from harness.tools.filesystem import WORKSPACE
from harness.tools.registry import tool


# Idea behind 60 is it can take longer time coz of network calls, installation etc
BASH_TIMEOUT = 60 # in seconds

# Command Allow List, empty means all command are allowed if not deny list
ALLOW_LIST: set[str] = { "ls", "cat", "grep", "wc", "python", "python3", "pip" }


# Command Deny List, if the command is in deny list it will not be performed, doesnt matter if it's in even allow list, somethin like IAM policy
DENY_LIST: set[str] = { "dd", "sudo", "mkfs", "pip" }


# Seprator
_CHAIN_SEPRATOR = ("&&", "||", "|", ";")

def _first_token(token: str) -> str:
  """Returns first whitespaced token of a command segment"""
  segment = token.strip()

  if not segment:
    return ""

  return segment.split()[0]

def segments(command: str) -> list[str]:
  """split the command into chain seprator into its segment

  This is a first token checker helper not a full shell parser, it wont catch every edge case(backticks, complex quoting)
  but can handle common chain pattern
  """

  segments = [command]

  for sep in _CHAIN_SEPRATOR:
    segments = [
      piece
      for seg in segments
      for piece in seg.split(sep)
    ]

  return segments


def _check_policy(command: str) -> str | None:
  """Check the command against allow or deny list.
  Return None if command is permitted or an error string if not,
  Deny list wins on conflict i.e a command on both list is rejected
  """

  tokens = [_first_token(s) for s in segments(command)]
  tokens = [t for t in tokens if t]

  if DENY_LIST:
    for token in tokens:
      if token in DENY_LIST:
        return f"[policy] '{token}' is in deny list refuse to run"

  if ALLOW_LIST:
    for token in tokens:
      if token not in ALLOW_LIST:
        return (
          f"[policy] the {token} is not in allow list"
          f"for now allow list allows "
          f"{', '.join(sorted(ALLOW_LIST)) }"        
        )

  return None



def _combine_output(stdout: str, stderr: str) -> str:
  """combines standard input and output for model"""

  stdout = stdout.strip()
  stderr = stderr.strip()

  if stdout and stderr:
    return f"{stdout}\n-----stderr-------\n{stderr}\n"

  return stdout or stderr


@tool
def bash(command: str) -> str:
  """
  Executes a bash command in the given workspace and returns the output in combined format

  Commands run within the workspace with complete interpretation applied - pipes, redirect, variable expansion and command chaining all work as it have actual terminal 

  can used for anything that filesystem or git tool cant cover: running script, invoking system utilities like grep, find, curl, wc, sort etc, installing packages (pip install, npm install), or executing code that has written to a file (python script.py, node server.js) etc

  Return stdout along with stderr (when not empty). Exit codes other than 0 are surfaced with [bash exit N] prefix so action can be taken by model based on the kind of code and recover

  Commands are subjected to allow list and deny list, if policy denies the command the command will return error instead of getting executed
  """
  policy_error = _check_policy(command)

  if policy_error:
    return policy_error
  

  try:
    result = subprocess.run(
      command,
      shell=True,
      cwd=WORKSPACE,
      capture_output=True,
      text=True,
      timeout=BASH_TIMEOUT,
      check=False
    )

  except subprocess.TimeoutExpired:
    return (
      f"[bash Timeout after {BASH_TIMEOUT}s] command was killed"
      f"If this was expected to take longer consider running it as sub tasks"
    )

  output = _combine_output(result.stdout, result.stderr) or "(no output)"

  if result.returncode != 0:
    return f"[bash exit {result.returncode}] {output}"

  return output

