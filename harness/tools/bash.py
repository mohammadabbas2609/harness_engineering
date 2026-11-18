"""Bash tool: A meta tool that will be used to execute bash command by giving agent access to shell"""

import subprocess
from harness.tools.filesystem import WORKSPACE
from harness.tools.registry import tool


# Idea behind 60 is it can take longer time coz of network calls, installation etc
BASH_TIMEOUT = 60 # in seconds

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
  """
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

