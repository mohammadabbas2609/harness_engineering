"""Cross session memory: the Agents.md pattern.

The harness reads Agents.md from the workspace at the start of the session and injects its content as the second system message. Agent uses existing tool `write` to update the file as it learns
"""

from harness.tools.filesystem import WORKSPACE
from harness.tools.registry import tool
from pathlib import Path
from openai import Client
from openai.types.chat import ChatCompletionMessageParam
from harness.config import COMPACTION_MODEL

# The Valid Categories that can be save in agents.md rest will be ignored/rejected
VALID_CATEGORIES = {
  "project_identities",
  "conventions",
  "decisions",
  "gotchas",
  "active_tasks"
}

# Map from valid categories to identifiers in agents.md
CATEGORY_HEADERS = {
  "project_identities":"## Project Identity",
  "conventions":"## Conventions",
  "decisions":"## Decisions",
  "gotchas":"## Gotchas",
  "active_tasks":"## Active Tasks"
}



AGENTS_MD_FILE_PATH = (WORKSPACE / "AGENTS.md")


AGENTS_MD_TEMPLATE = """# Project Memory

> This file is the agent's durable memory across sessions. The harness
> loads it at the start of every session. Updates happen two ways:
> the `remember(category, entry)` tool for in-session writes, and an
> end-of-session consolidation step that reviews the whole conversation
> and updates this file before the sandbox tears down.

## Project Identity
(What is this project? What does it do? Who is it for?)

## Conventions
(Code style, naming patterns, libraries used, tool preferences.)

## Decisions
(Choices that have been made and the reasoning behind them.)

## Gotchas
(Things to remember about this codebase that might trip up future
sessions — quirks, non-obvious dependencies, common mistakes.)

## Active Tasks
(What's currently being worked on. Clear entries when work completes.)
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


def _validate_agent_md_structure(text: str) -> bool:
  """Check if all above mentioned sections are present or not
  Returns True if it is valid othwerwise false
  
  """

  return all(header in text for header in CATEGORY_HEADERS.values())


def _save_agents_md(text: str) -> None:
  """Atomically writes the Agents.md as the given text uses write-to-temp-then-rename strategy 
    to make sure either the whole writes lands or none
  """
  tmp_path = AGENTS_MD_FILE_PATH.with_suffix(".md.tmp")
  tmp_path.write_text(text)
  tmp_path.replace(AGENTS_MD_FILE_PATH)


@tool
def remember(category: str, text: str) -> str:
  """
  Adds an entry to specific section of agents.md file 

  Use this to record something durable during the session - project fact learned, convention observed, decision made, gotcha encountered, any task in progress, entry append to the named section; existing entries are preserved

  Categories:
  - Project Identity: What is this project? What does it do? Who is it for?
  - Conventions: Code style, naming patterns, libraries used, tool preferences.
  - Decisions: Choices that have been made and the reasoning behind them.
  - Gotchas: Things to remember about this codebase that might trip up future
    sessions quirks, non-obvious dependencies, common mistakes.
  - Active Tasks: What's currently being worked on. Clear entries when work completes.
  """

  if category not in VALID_CATEGORIES:
    VALID = ", ".join(sorted(VALID_CATEGORIES))
    return f"[remember] {category} is not valid, only categories that are valid {VALID}"

  current = load_agentmd_file()

  header = CATEGORY_HEADERS[category]

  if header not in current:
    return f"[remember] {header} is missing in Agents.md file. Aborting write"

  lines = current.split("\n")

  new_lines = []

  inserted = False

  for line in lines:
    new_lines.append(line)
    if line == header and not inserted:
      new_lines.append(f"- {text}")
      inserted = True

  updated = '\n'.join(new_lines)

  _save_agents_md(updated)

  return f"[remember] added to {category}"


def consolidate_memory(messages: list, client: Client) -> None:
  """
    Run end-of-the-memory consolidation step

    Sends the current Agents.md + full session history + consolidation prompt to the model
    Expects a complete Agents.md rewrite back. Validates a structure before writing, On failure logs and keeps the same version of file 
  """

  print("Consolidating Memory ...")

  consolidation_prompt = (Path(__file__).parent.parent / 'prompts' / 'session_end_memory.txt').read_text()

  try:
    current_agent_md = load_agentmd_file()
    consolidation_context = (
      f"{consolidation_prompt}\n\n"
      f"==== Current AGENTS.md ===== \n\n {current_agent_md}"
    )

    consolidated_messages: list[ChatCompletionMessageParam] = messages + [
      {
        "role": "system", "content": consolidation_context
      }
    ]

    response = client.chat.completions.create(
      model=COMPACTION_MODEL,
      messages=consolidated_messages
    )

    proposed = response.choices[0].message.content

    if not proposed:
      print(
        "Memory consolidation returned empty content. Keeping the current version of AGENTS.md"
      )
      return

    print(f"consolidated text \n\n {proposed}")

    if not _validate_agent_md_structure(proposed):
      print(
        "Memory consolidation returned malformed structure",
        "Missing section header keeping current version of AGENTS.md file"
      )
      return

    _save_agents_md(proposed)
    print("Memory updated...")

  except Exception as e:
    print(f"Memory consolidation failed: {e}. Keeping current AGENTS.md.")






