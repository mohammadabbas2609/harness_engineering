"""Bash tool: A meta tool that will be used to execute bash command by giving agent access to shell"""

import subprocess
from harness.tools.filesystem import WORKSPACE
from harness.tools.registry import tool
from harness.config import BASH_TIMEOUT, ALLOW_LIST, DENY_LIST
from harness.sandbox import Sandbox


_sandbox : Sandbox | None = None

def set_sandbox(sb: Sandbox) -> None:
  """isko call krenge from agent.py to wire this up in this module"""
  global _sandbox
  _sandbox = sb

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

    if _sandbox is None:
      return (
        "[sandbox not initialized this is internal bug]; please create issue on github"
        "agent.py should've called it at startup"
      )

    exit_code, stdout, stderr =  _sandbox.execute(command=command)

    output = _combine_output(stdout, stderr) or "(no output)"

    if exit_code != 0:
      return f"[bash exit {exit_code}] {output}"

    return output
  
  except Exception as e:
    
    return f"[bash error] soemthing went wrong {e}"


