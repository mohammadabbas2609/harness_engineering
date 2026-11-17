"""File System tools that read write edit given file bounded within workspace"""


from pathlib import Path
from harness.tools.registry import tool


WORKSPACE = Path("D:/harness-engineerin/loop/workspace").resolve()


# Idempotent Operation
WORKSPACE.mkdir(exist_ok=True)


def _resolve_path(path: str) -> Path:
  """
    Resolve path in the given workspace and confirm it stays inside it only

    Raises ValueError if it tries to escape workspace directory - this is the hard constriant that prevents the agent form reading or modifying anything outside of the sandbox  
  """

  target = (WORKSPACE / path).resolve()

  if not target.is_relative_to(WORKSPACE):
    raise ValueError(f"{path} is not bounded within {WORKSPACE}")

  return target


@tool
def read(path: str) -> str:
  """Reads the content of file within the workspace. by path"""
  return _resolve_path(path).read_text()


@tool
def write(path: str, content: str) -> str:
  """Writes content in the file, creates if file dont exist, Overwrites the file if already exist, return bytes count as the confirmation that content was written in the file at given path"""

  target = _resolve_path(path)

  target.parent.mkdir(exist_ok=True, parents=True)

  target.write_text(content)

  return f"wrote {len(content)} bytes to {path}"


@tool
def list(path: str = '.') -> str:
  """List the files and directories in the given path inside the workspace, default to root in the workspace, returns one entry per line"""

  target = _resolve_path(path)

  if not target.is_dir():
    return f"error: {path} is not a directory"

  entries = sorted(target.iterdir())

  return '\n'.join(e.name + ("/" if e.is_dir() else "") for e in entries)


@tool
def create_directory(path: str) -> str:
  """creates a directory in the given workspace produces including the parent directory too, no error if direcotry already exists"""

  target = _resolve_path(path)

  target.mkdir(parents=True, exist_ok=True)

  return f"created directory {path}"


@tool
def delete(path: str) -> str:
  """Deletes the file in the given workspace, it does not deletes directory"""

  target = _resolve_path(path)

  if target.is_dir():
    return f"cant delete {path} as it is directory"

  target.unlink()

  return f"file {path} deleted successfully" 