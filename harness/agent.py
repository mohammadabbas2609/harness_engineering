from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import json
from harness.tools import registry
from typing import cast

from harness.memory import load_agentmd_file

load_dotenv()

MODEL = "gpt-4o-mini"
client = OpenAI()


# The amount of tool call per user turn the model can do, when hit the harness forces the model to summarize what it did and hand back the control to user instead of running loop infinitely
STEP_BUDGET = 25

BUDGET_SURPASSED_MESSAGE = f"""
You reached the step budget for this turn ({STEP_BUDGET} tool call). Do not make any tool call instead hand the control back to user with 

- What you accompolished in this turn ?
- What is pending ?
- What user should ask next to continue the work ?

Your response will be the final message in this turn. The user will reply and you can continue from there
"""


SYSTEM_PROMPT = """
You're an coding assistant running in terminal, helping a devloper in thier software engineering tasks. 

Be concise, and prefer short direct answers over long verbose one, when the user asks for code, return the code with minimal explanation, unless they ask for more verbose one

when returning code, use fenced block and specify the language.

You currently have access to following file system tools: read, write, list, create_directory, delete tool scoped to a workspace directory, use them whenever tasks involves reading, modifying or organizing a file. Path are relative to workspace root. Prefer reading and writing file over describing them in coversation.

You also have access to following git tools for versioning your work: 
git_status, git_diff, git_log, git_commit, git_checkout, git_branch and git_merge. Please note: git is already initiliazed in workspace
- commit frequently, small easy focused commit that are easy to rollback
- commit before doing any risky change, so you get the checkpoint to restore if things dont work out
- meaningful commit message: it should describe what's change, what it impacts
- use branches to create any independent feature and then merge it back

You also have access to one more tool: `bash`. It executes shell commands in the           
workspace with full shell interpretation — pipes, redirects, and command
chaining all work. Use bash for anything the specific tools above don't
cover: running scripts (python foo.py, node foo.js), invoking system
utilities (grep, find, curl, wc, sort, awk), installing packages
(pip install ...), or exploring the environment (ls, pwd, which python).

Prefer the specific tools when they apply. If the task is to read a
file, use `read`, not `bash("cat file.md")`. If the task is to commit,
use `git_commit`, not `bash("git commit ...")`. The specific tools are
safer, faster, and clearer to trace. Reach for `bash` when the specific
tools don't cover what you need — which is often, because software work
is varied.

Bash commands see the workspace as their working directory. `cd` inside
a bash command does not persist to the next tool call; each bash
invocation starts fresh from the workspace root.

Workspace also consist of AGENTS.md file, your durable memory across sessions. It is loaded in your context at very start of each session, update it whenever you learn something worth remembering for future sessions, like project context, conventions, gotchas, active tasks and future tasks (if it is worth remembering), also please preserve the exisiting structure whie updating it.
"""


def run():
  """run this loop until the user ends the conversation"""

  try:

    # Load the agent.md file before any interaction happens
    agent_md_file = load_agentmd_file()

    messages: list[ChatCompletionMessageParam] = [
      {
        "role":"system",
        "content":SYSTEM_PROMPT
      },
      {
        "role":"system",
        "content":agent_md_file
      }
    ]

    print("Welcome to idk, type quit or exit to end this session \n")

    while True:

      user_input = input("> ").strip()

      if user_input in {"quit", "exit"}:
        print("Good Bye!!")
        break

      if not user_input:
        continue

      messages.append({ "role":"user", "content":user_input })


      step_count = 0

      while True:
        response = client.chat.completions.create(
          model=MODEL,
          messages=messages,
          tools=registry.get_schemas()
        )
                
        message = response.choices[0].message

        if not message.tool_calls:
          break

        if step_count >= STEP_BUDGET:
          
          messages.append({
            "role":"system",
            "content":BUDGET_SURPASSED_MESSAGE
          })

          response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=registry.get_schemas()
          )

          break

        messages.append(cast(ChatCompletionMessageParam, message.model_dump(exclude_none=True)))

        for call in message.tool_calls:

          if call.type != "function":
            raise NotImplementedError(
                f"Unsupported tool type: {call.type}"
            )
          
          print("**Tool Calling** \n")
          print(f"calling tool {call.function.name} with foll args {call.function.arguments}\n")

          arguments = json.loads(call.function.arguments)
          result = registry.dispatch(name=call.function.name, arguments=arguments)
          
          print(f"result of the tool {result}\n")
          print("**Tool Calling Ended** \n")
          
          messages.append({
            "role":"tool",
            "tool_call_id": call.id,
            "content":result 
          })

        step_count += 1

      if not message.content:
        raise RuntimeError(
          "Loop terminated but message.content is empty",
          "Check API response and termination block to resolve"
        )

      assistant_text = message.content

      messages.append({ "role":"assistant", "content": assistant_text })

      print(f"AI> {assistant_text}\n")
  
  except KeyboardInterrupt:

    print("good bye !!")




if __name__ == "__main__":
  run()