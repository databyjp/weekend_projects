# Better Context

RAG system for documentation search using Weaviate. Crawls documentation websites, chunks content, stores in a vector database, and provides semantic search through an MCP server.

## Setup

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- API Keys: `COHERE_API_KEY`, `ANTHROPIC_API_KEY` (set as environment variables)

### Installation
```bash
# Start Weaviate
docker-compose up -d

# Install dependencies
uv sync
```

## Usage

### 1. Crawl Documentation
```bash
python 1_get_docs.py
```
Crawls `docs.weaviate.io` and saves to `./output/weaviate_docs_crawl4ai.json`

### 2. Index Documents
```bash
python 2_index_docs.py
```
Chunks documents and indexes them in Weaviate with Cohere embeddings

### 3. Test RAG Query
```bash
python 3_check_rag.py
```
Example query using Weaviate's generative module with Claude

### 4. Run MCP Server
```bash
python 4_build_mcp.py
```
Starts the MCP server that exposes `search_weaviate_docs` tool

### 5. Agent Example
```bash
python 5_agent_example.py
```
Demonstrates using the MCP server with pydantic-ai to answer Weaviate questions

## Architecture

**Pipeline**: Crawl ’ Chunk ’ Index ’ Retrieve

- **Crawler**: crawl4ai (BFS, depth 4)
- **Chunker**: chonkie TokenChunker (512 tokens, 128 overlap)
- **Vector DB**: Weaviate with Cohere embed-v4.0
- **MCP Server**: Returns raw chunks for agent-side generation
- **Agent**: pydantic-ai with Claude 3.5 Haiku

## Configuration

Edit these files to customize:
- `1_get_docs.py:8` - Change crawl domain
- `2_index_docs.py:17-20` - Adjust chunk size/overlap
- `4_build_mcp.py` - Modify MCP tool behavior
- `5_agent_example.py:20-35` - Customize agent system prompt

## Utilities

```bash
# Reset database
python 0_reset_db.py
```
