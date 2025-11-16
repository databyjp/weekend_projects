# Weaviate Agentic Memory Demo

This demo showcases how to use [Weaviate](https://weaviate.io/) as an agentic memory layer for a conversational AI. It demonstrates patterns for extracting, consolidating, and retrieving information to give an AI assistant a persistent, evolving memory.

The core logic involves:
1.  **Extracting** salient facts from conversations.
2.  **Consolidating** new facts with existing memories by adding, updating, or invalidating old information.
3.  **Retrieving** relevant memories to provide context for new responses.

## Setup

1.  **Install dependencies:**
    ```bash
    uv pip sync
    ```

2.  **Set Environment Variables:**
    ```bash
    export ANTHROPIC_API_KEY="..."
    export WEAVIATE_URL="..."
    export WEAVIATE_API_KEY="..."
    export COHERE_API_KEY="..." # For Weaviate's text2vec-cohere module
    ```

## Usage

*   **Run Chat:** `python basic.py`
    *   Log in or create a user.
    *   In-chat commands: `/memories`, `/invalidated`, `/quit`.
*   **Reset Memory:** `python basic_reset_memory.py` (Deletes the Weaviate "Memory" collection).

## Example Conversation

> **User**: I'm looking to run a half marathon in 5 months. I'm in Edinburgh and it's cold.
>
> *Memory created: User is in Edinburgh.*
>
> **User**: It's January now. I've moved to Australia for Jan and Feb.
>
> *Memory invalidated: User is in Edinburgh. -> Memory created: User is in Australia.*
>
> **User**: It's May. I've run my race, moved to Portugal permanently, and want to do weight training.
>
> *Memories invalidated: User is in Australia, user is running. -> Memories created: User lives in Portugal, user is interested in weight training.*
