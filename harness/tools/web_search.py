"""Web Search Tool via tavily API which is optimized for LLM web searches

Basically it is used to fill the temporal knowledge gap of model
"""

import os
from tavily import TavilyClient


from harness.tools.registry import tool
from harness.config import WEBSEARCH_MAX_RESULT


def _format_results(response: dict, query: str) -> str:
  """
    Convert Tavily JSON response to markdown text for model 

    Structure: LLM generated answer query on top (usually the direct answer), then a numbered list of ranked sources with title url and snippet
  """

  answer = response.get("answer") or "(no answer synthesized)"

  results = response.get("results") or []

  lines = [f"Web Search result for : {query}", "", "**Answer**", answer, ""]

  if results:
    lines.append("**Sources**")
    for i,result in enumerate(results, start=1):
      title = result.get("title") or "(untitled)"
      url = result.get("url", "")
      content = result.get("content", "").strip()
      lines.append(f"{i}. Title {title} -- URL {url}")
      if content:
        lines.append(f" {content}")

  else:
    lines.append("No sources returned")


  return "\n".join(lines)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information and return ranked results.

    Use this when the answer requires information the model wouldn't know
    from training — post-cutoff events, current software versions, recent
    releases, moving-target facts (prices, availability, official
    announcements). Also useful for verifying claims where accuracy
    matters.

    Do NOT use for information the model reliably knows (well-established
    facts, general programming knowledge), for things in the workspace
    (read the files instead), or for things in AGENTS.md (already in
    context). Search consumes API quota and adds latency; use it when it
    earns its place.

    Args:
        query: A specific, focused search query. Prefer natural phrasing
            over keyword-stuffing ("what version is the current node LTS"
            works better than "node lts version current").
        max_results: How many source results to return. Defaults to 5.
            Use fewer for narrow lookups, more for broader research.

    Returns:
        Formatted text with an answer summary followed by the ranked
        source list. Each source has title, URL, and a snippet.
    """
    if max_results is None:
        max_results = WEB_SEARCH_MAX_RESULTS

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return (
            "[web_search error] TAVILY_API_KEY is not set. Get a key at "
            "tavily.com (free tier: 1000 requests/month) and add it to "
            "your .env file as: TAVILY_API_KEY=tvly-your-key-here"
        )

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
        )
    except Exception as e:
        return f"[web_search error] Search failed: {e}"

    return _format_results(response, query)