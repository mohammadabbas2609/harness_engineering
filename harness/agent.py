from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pathlib import Path
import json
from typing import cast
from harness.tools import registry
from harness.config import STEP_BUDGET, MODEL
from harness.memory import (
  load_agentmd_file,
  consolidate_memory
)
from harness.sandbox import Sandbox
from harness.tools.bash import set_sandbox 


load_dotenv()

client = OpenAI()

BUDGET_SURPASSED_MESSAGE = f"""
You reached the step budget for this turn ({STEP_BUDGET} tool call). Do not make any tool call instead hand the control back to user with 

- What you accompolished in this turn ?
- What is pending ?
- What user should ask next to continue the work ?

Your response will be the final message in this turn. The user will reply and you can continue from there
"""


SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.txt").read_text()


def run():
  """run this loop until the user ends the conversation"""

  # Setting up the sandbox so the agent ops is done in container rather than polluting host machine
  print("===================================")
  print("Setting up the environment ...")
  
  sandbox = Sandbox()
  sandbox.start()
  set_sandbox(sandbox)

  print("====================================")


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
        consolidate_memory(messages=messages, client=client)
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

  except Exception as e:
    print(f"Something went wrong ... {e}")

  finally:
    print("Clearing sandbox ...")
    # Stop the sandbox
    sandbox.stop()




if __name__ == "__main__":
  run()