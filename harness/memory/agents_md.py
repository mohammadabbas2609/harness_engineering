"""Cross session memory: the Agents.md pattern.

The harness reads Agents.md from the workspace at the start of the session and injects its content as the second system message. Agent uses existing tool `write` to update the file as it learns
"""

from harness.tools.filesystem import WORKSPACE


AGENTS_MD_FILE_PATH = (WORKSPACE / "AGENTS.md")


AGENTS_MD_TEMPLATE = """\

# Project Memory

> Following file is the agent's durable memory access across the session
> harness loads it at starts of every session. Update it whenever you learn
> Something worth remembering for future session

## Project Context

> What is this Project ? What does it do ? Who is it for ?

## Conventions

> Code Style, naming patterns, libraries used, tools preferences

## Gotchas

> Things to remeber in codebase that may steer the future sessions (quirks, non obvious dependencies, common mistakes.)

## Active Tasks

> What you're currently working on. Clear entries when work is complete

"""

def load_agentmd_file() -> str:
  """Reads AGENTS.md from the workspace. creating it form above template if missing

  Returns the whole file as a string, ready to be used as the content in the system message
  """

  if not AGENTS_MD_FILE_PATH.exists():
    AGENTS_MD_FILE_PATH.write_text(AGENTS_MD_TEMPLATE)

  text = ''

  with open(AGENTS_MD_FILE_PATH, 'r') as agent_file:
    text += agent_file.read()

  return text
