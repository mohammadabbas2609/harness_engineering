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

Workspace also consist of AGENTS.md file, your durable memory across sessions. It is loaded in your context at very start of each session, update it whenever you learn something worth remembering for future sessions, like project context, conventions, gotchas, active tasks and future tasks (if it is worth remembering), also please preserve the exisiting structure whie updating it.
"""


def run():
  """run this loop until the user ends the conversation"""

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

    response = client.chat.completions.create(
      model=MODEL,
      messages=messages,
      tools=registry.get_schemas()
    )
              
    message = response.choices[0].message

    if message.tool_calls:
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

      response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=registry.get_schemas()
      )
          
      message = response.choices[0].message

    assistant_text = message.content or "(not output: only tool used)"

    messages.append({ "role":"assistant", "content": assistant_text })

    print(f"AI> {assistant_text}\n")




if __name__ == "__main__":
  run()