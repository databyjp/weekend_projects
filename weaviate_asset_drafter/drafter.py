# Reference: https://ai.pydantic.dev/agents/
from pydantic_ai import Agent
from pathlib import Path
from pydantic_ai.mcp import MCPServerStdio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

weaviate_docs_mcp_directory = Path.home() / "code" / "weekend_projects/better_context"
weaviate_docs_mcp_server = MCPServerStdio(
    command="uv",
    args=["--directory", str(weaviate_docs_mcp_directory), "run", "python", "4_build_mcp.py"],
    env=os.environ.copy(),
)

basic_agent = Agent(
    model="claude-haiku-4-5-20251001",
    toolsets=[weaviate_docs_mcp_server]
)


@basic_agent.system_prompt
def set_system_prompt() -> str:
    return f"""
    You are an expert writer who is also very knowledgeable about Weaviate.
    Your job includes writing supplementary materials for Weaviate's educators.

    These materials should help educators teach
    developers about Weaviate, and how to use it effectively,
    through the use of theoretical explanations and practical examples.

    You have access to the Weaviate documentation via a set of tools.
    Use these tools to look up any information you need about Weaviate.

    Only produce the requested output. Do not include any other text.
    """


for prompt in [
    f"""
Write a set of slides explaining multi-tenancy in Weaviate.

The slides' format should be for Spectacle, the React-based slide deck framework.
When creating the project with Spectacle, I used:
`npx create-spectacle`, and chose `Markdown` as the option.

Write the file that I can replace "slides.md" with.

Limit the output to 5 slides.

The slides are to include:

- What is multi-tenancy in Weaviate
- Practical problems addressed by multi-tenancy
- Example use cases for multi-tenancy in Weaviate
- How to use multi-tenancy in Weaviate (include Python code examples)
    - Collection definition
    - Tenant creation
    - Data ingestion
    - Queries
- Best practices for multi-tenancy in Weaviate
    """,
]:
    print(f">> RUNNING PROMPT: {prompt}")
    model_response = basic_agent.run_sync(user_prompt=prompt)
    print(f"Agent response:")
    print(model_response.output, "\n\n")
    with open("multi-tenancy/slides.md", "w") as f:
        f.write(model_response.output)
