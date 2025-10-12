# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demo application to show off a use case of Weaviate. It is a RAG (Retrieval-Augmented Generation) system that crawls documentation websites, chunks the content, stores it in a Weaviate vector database, and provides contextual help for developers through an MCP server. The project is designed to create an MCP (Model Context Protocol) server for enhanced documentation retrieval.

## Setup and Environment

The project uses:
- **Python 3.10+** with `uv` for dependency management
- **Docker Compose** for running Weaviate locally
- **API Keys Required**: Set `COHERE_API_KEY` and `ANTHROPIC_API_KEY` as environment variables

### Start Weaviate Database
```bash
docker-compose up -d
```

The Weaviate instance runs on `http://localhost:8080` with anonymous access enabled.

### Install Dependencies
```bash
uv sync
```

## Development Workflow

The project follows a numbered script workflow (0-5) that represents the data pipeline stages and usage example:

### 1. Reset Database (`0_reset_db.py`)
```bash
python 0_reset_db.py
```
Deletes the "Chunks" collection from Weaviate. Use this to start fresh.

### 2. Crawl Documentation (`1_get_docs.py`)
```bash
python 1_get_docs.py
```
- Uses `crawl4ai` to crawl `docs.weaviate.io`
- BFS strategy with max depth of 4
- Outputs to `./output/weaviate_docs_crawl4ai.json`
- Results are cached for faster re-runs

### 3. Index Documents (`2_index_docs.py`)
```bash
python 2_index_docs.py
```
- Chunks the crawled docs using `chonkie` (TokenChunker with 512 tokens, 128 overlap)
- Creates Weaviate "Chunks" collection if it doesn't exist
- Uses Cohere's `embed-v4.0` model for vectorization
- Stores chunks with metadata: `chunk`, `chunk_no`, `path`
- Uses deterministic UUID generation for idempotent inserts

### 4. Test RAG Query (`3_check_rag.py`)
```bash
python 3_check_rag.py
```
- Performs hybrid search on the "Chunks" collection
- Uses Claude 3.5 Haiku for generation via Weaviate's generative module
- Example query about Weaviate collection aliases

### 5. Run MCP Server (`4_build_mcp.py`)
```bash
python 4_build_mcp.py
```
Runs the MCP server that exposes the RAG functionality as a tool. The server communicates via stdio and provides:
- **Tool**: `search_weaviate_docs` - Searches the indexed documentation and returns relevant chunks
- **Parameters**: `query` (required), `limit` (optional, default: 5)
- **Returns**: Raw chunk objects with `chunk`, `chunk_no`, and `path` properties

To use with Claude Desktop, add to your MCP configuration:
```json
{
  "mcpServers": {
    "weaviate-docs": {
      "command": "uv",
      "args": ["run", "python", "/path/to/better_context/4_build_mcp.py"],
      "env": {
        "COHERE_API_KEY": "your-key"
      }
    }
  }
}
```

### 6. Agent Example (`5_agent_example.py`)
```bash
python 5_agent_example.py
```
Demonstrates using the MCP server with `pydantic-ai` to create an agent that can answer Weaviate questions:
- Connects to the MCP server using `MCPServerStdio`
- Creates an agent with Claude 3.5 Haiku that uses the search tool
- System prompt emphasizes using tools over internal knowledge for up-to-date code examples
- Example query about vector compression methods with end-to-end code examples

## Architecture

### Data Flow
1. **Crawling**: `crawl4ai` → domain-filtered crawl → JSON output with URLs as keys
2. **Chunking**: `chonkie` TokenChunker → overlapping text chunks
3. **Indexing**: Weaviate batch insert → Cohere embeddings → vector DB
4. **Retrieval**: Hybrid search (vector + keyword) → Claude generation → answers with sources

### Key Components

**Chunking Strategy**: Currently uses `TokenChunker` (word-based, 512 tokens, 128 overlap). A `NeuralChunker` option is commented out in `2_index_docs.py` for semantic-aware chunking.

**Vector Configuration**: The "Chunks" collection uses Cohere's `text2vec_cohere` with `embed-v4.0`, vectorizing both `chunk` and `path` properties.

**UUID Strategy**: Uses `generate_uuid5("Chunks", f"{path}-{i}")` for deterministic chunk IDs, enabling re-indexing without duplicates.

### Weaviate Collection Schema
```python
{
    "name": "Chunks",
    "properties": [
        {"name": "chunk", "data_type": "TEXT"},
        {"name": "chunk_no", "data_type": "INT"},
        {"name": "path", "data_type": "TEXT", "tokenization": "FIELD"}
    ],
    "vector_config": "text2vec_cohere (embed-v4.0)"
}
```

## Configuration Notes

- **Crawler**: Configured for `docs.weaviate.io` domain only. To crawl other docs, modify `allowed_domains` in `1_get_docs.py:8`
- **Chunk Size**: Adjust `chunk_size` and `chunk_overlap` in `2_index_docs.py:17-20`
- **Batch Size**: Set to 50 objects per batch in `2_index_docs.py:49`
- **RAG Model**: Currently uses `claude-3-5-haiku-latest` in `3_check_rag.py:16`

## MCP Server and Agent Usage

The MCP server (`4_build_mcp.py`) exposes a single tool for searching the documentation chunks. Unlike the test script in `3_check_rag.py` which uses Claude generation directly, the MCP server returns raw chunks and delegates the generation to the calling agent.

**Tool Schema**:
- **Name**: `search_weaviate_docs`
- **Input**: `query` (string), `limit` (integer, optional, default: 5)
- **Output**: Raw chunk objects with `chunk`, `chunk_no`, and `path` properties
- **Connection**: Creates/closes Weaviate client per request to avoid connection pooling issues

**Agent Pattern** (`5_agent_example.py`):
The agent example shows the recommended usage pattern:
1. MCP server provides retrieval tool (returns chunks only)
2. Agent (pydantic-ai) decides when to call the tool
3. Agent's LLM synthesizes the chunks into coherent answers
4. System prompt instructs agent to prefer tool results over internal knowledge

This separation allows the agent's LLM to handle generation, while the MCP server focuses purely on retrieval.
