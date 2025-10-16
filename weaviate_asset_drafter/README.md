# Weaviate Asset Drafter

AI-powered tool for generating educational materials about Weaviate. Uses an MCP-enabled agent to access Weaviate documentation and draft slides, tutorials, and other teaching assets.

## Setup

### Prerequisites
- Python 3.10+
- Node.js (for Spectacle slide generation)
- API Keys: `COHERE_API_KEY`, `ANTHROPIC_API_KEY` (set as environment variables)
- Running Weaviate documentation MCP server (from `../better_context`)

### Installation
```bash
# Install Python dependencies
uv sync

# For slide generation, initialize Spectacle project
cd multi-tenancy
npx create-spectacle
# Choose "Markdown" when prompted
```

## Usage

### Generate Educational Materials
```bash
python drafter.py
```
Generates educational content based on prompts defined in the script. Current example creates a multi-tenancy slide deck.

## Architecture

**Agent Flow**: MCP Client ’ Documentation Search ’ Claude Generation ’ Formatted Output

- **Agent**: pydantic-ai with Claude Haiku 4.5
- **MCP Connection**: Accesses Weaviate docs via `better_context` MCP server
- **Output Format**: Spectacle-compatible Markdown slides
- **System Prompt**: Configured for expert educational content writing

## Configuration

Edit `drafter.py` to customize:
- Line 11: Change path to Weaviate docs MCP server
- Line 19: Adjust Claude model version
- Lines 41-64: Modify prompts for different educational materials
- Line 70: Change output file path

## Current Output

The script generates:
- **multi-tenancy/slides.md**: 5-slide deck covering:
  - Multi-tenancy concepts in Weaviate
  - Practical problems and use cases
  - Python code examples (collection setup, tenant creation, data ingestion, queries)
  - Best practices

## Extending the Tool

Add new prompts to the loop at line 41 to generate:
- Tutorial notebooks
- Workshop materials
- Code example repositories
- Documentation supplements
- Training presentations

The agent automatically references the latest Weaviate documentation through the MCP server to ensure accuracy.
