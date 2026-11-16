"""Tool registry, stores tools, generates schemas, dispacthes calls"""

from dataclasses import dataclass
from typing import Any, Callable, get_type_hints
from pydantic import create_model
import inspect

@dataclass
class Tool:
  """
    A registered tool, wraps a function with its metadata
  """
  name: str
  description: str
  function: Callable
  schema: dict

class ToolRegistry:
  """
    Holds tools, exposes thier schema, dispatches tool call
  """

  def __init__(self) -> None:
    self._tools: dict[str, Tool] = {}

  def register(self, tool: Tool) -> None:
    self._tools[tool.name] = tool

  def get_schemas(self) -> list[dict]:
    """Returns the schemas of tools in OpenAI format"""
    schemas = []

    for tool in self._tools.values():
      schemas.append(
        {
          "type":"function",
          "function":{
            "name": tool.name,
            "description":tool.description,
            "parameters":tool.schema
          }
        }
      )

    return schemas

  def dispatch_schema(self, name: str, arguments: dict[str, Any]) -> str:


    if name not in self._tools:
      return f"error: unknown tool {name} specified"

    try:
      result = self._tools[name].function(**arguments)
      return str(result)
    except Exception as e:
      return f"error: {type(e).__name__}:{e}"
    

registry = ToolRegistry()


def tool(func: Callable) -> Callable:

  """
    Registers a function as a tool

    Reads the function name its docstring, and type hinted parameters and build the openAI schema and adds it to the global registry
  """

  name = func.__name__
  description = inspect.getdoc(func) or ''


  signature = inspect.signature(func)
  hints = get_type_hints(func)

  # Build Pydantic model fields
  fields = {}

  for param_name, param in signature.parameters.items():
    param_type = hints.get(param_name, Any)

    if param.default == inspect.Parameter.empty:
        fields[param_name] = (param_type, ...)
    else:
        fields[param_name] = (param_type, param.default)

  # Create a Pydantic model dynamically
  ArgsModel = create_model(f"{name}Arguments", **fields)

  # Generate JSON schema
  schema = ArgsModel.model_json_schema()


  registry.register(
    Tool(
      name=name, 
      description=description, 
      schema=schema, 
      function=func
  ))

  return func