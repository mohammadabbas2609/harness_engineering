from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"
client = OpenAI()


def run():
  """run this loop until the user ends the conversation"""
  messages = []

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