from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"
client = OpenAI()


SYSTEM_PROMPT = """
You're an coding assistant running in terminal, helping a devloper in thier software engineering tasks. 

Be concise, and prefer short direct answers over long verbose one, when the user asks for code, return the code with minimal explanation, unless they ask for more verbose one

when returning code, use fenced block and specify the language.

You dont currently have access to any tool, you cannot read, write files run any bash commands or modify any thing on users system, if user asks for anything that requires tool, say so plainly and suggest them to copy paste relevant chunk so you can act upon it.
"""


def run():
  """run this loop until the user ends the conversation"""
  messages = [
    {
      "role":"system",
      "content":SYSTEM_PROMPT
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
    )
    
    ai_message = response.choices[0].message.content

    print(f"AI > {ai_message}\n")

    messages.append({ "role":"assistant", "content":ai_message })




if __name__ == "__main__":
  run()