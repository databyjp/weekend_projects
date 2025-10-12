import os
import asyncio
import weaviate
from weaviate.classes.generate import GenerativeConfig
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


app = Server("weaviate-docs")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_weaviate_docs",
            description="Search Weaviate documentation and get chunks of relevant text",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or search query about Weaviate"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "search_weaviate_docs":
        raise ValueError(f"Unknown tool: {name}")

    query = arguments["query"]
    limit = arguments.get("limit", 5)

    client = weaviate.connect_to_local(
        headers={
            "X-Cohere-Api-Key": os.getenv("COHERE_API_KEY")
        },
    )

    try:
        chunks = client.collections.use("Chunks")

        response = chunks.query.hybrid(
            query=query,
            limit=limit,
        )

        objs = [o.properties for o in response.objects]

        return [TextContent(
            type="text",
            text=str(objs)
        )]

    finally:
        client.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
