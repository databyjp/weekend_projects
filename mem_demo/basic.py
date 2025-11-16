import anthropic
import weaviate
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections import Collection
import os
import json
from uuid import uuid4
from datetime import datetime, timezone
import typer
import questionary
import textwrap

anthropic_client = anthropic.Anthropic()

EXTRACTION_PROMPT_TEMPLATE = textwrap.dedent(
    """
    Existing memories: {memories_text}

    New exchange:
    User: {user_message}
    Assistant: {assistant_response}

    Extract NEW or CHANGED facts not already accurately captured
    in existing memories.

    - NEW: Information not in existing memories
    - CHANGED: Updates or contradictions to existing memories
    - SKIP: Information already accurately captured

    Extract: preferences, personal facts, plans
    Ignore: greetings, questions, general knowledge

    IMPORTANT: Each fact must be atomic - one complete idea per fact.
    Break compound statements into separate facts.

    Examples:
    ✓ Good: ["User is vegetarian", "User lives in Berlin"]
    ✗ Bad: ["User is vegetarian and lives in Berlin"]

    Return JSON: {{"facts": ["fact1", "fact2"]}}
    """
)

CONSOLIDATION_PROMPT_TEMPLATE = textwrap.dedent(
    """
    New fact: {fact}
    Existing memories: {existing_memories}

    Choose one action:
    - ADD: Completely new information not related to existing memories
    - UPDATE: Refines or adds detail to existing memory without contradicting it
    - INVALIDATE: Contradicts existing memory (old info is now false/outdated)
    - NOOP: Information already accurately captured

    For UPDATE: provide updated_content and target_uuid
    For INVALIDATE: provide target_uuid (old memory will be marked invalid, new fact added)

    Always explain your reasoning for the chosen action. Be succinct when possible.

    Return JSON with your decision.
    """
)


def connect_to_weaviate():
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=os.getenv("WEAVIATE_API_KEY"),
        headers={"X-Cohere-Api-Key": os.getenv("COHERE_API_KEY")},
    )


def get_or_create_collection(db_client: weaviate.WeaviateClient):
    """Get or create the memory collection"""

    if not db_client.collections.exists("Memory"):
        return db_client.collections.create(
            name="Memory",
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="invalidation_time", data_type=DataType.DATE),
            ],
            multi_tenancy_config=Configure.multi_tenancy(auto_tenant_creation=True),
            vector_config=Configure.Vectors.text2vec_cohere(
                source_properties=["content"],
                quantizer=Configure.VectorIndex.Quantizer.rq(),
            ),
            inverted_index_config=Configure.inverted_index(
                index_timestamps=True, index_null_state=True
            ),
        )
    else:
        return db_client.collections.use("Memory")


def extract_and_consolidate(
    user_id: str,
    user_message: str,
    assistant_response: str,
    memories_text: str,
    memory_collection: Collection,
):
    """Extract facts from conversation and consolidate with existing memories"""
    user_memories = memory_collection.with_tenant(user_id)

    # STEP 1: Extract - What's worth remembering?
    extraction = anthropic_client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        betas=["structured-outputs-2025-11-13"],
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT_TEMPLATE.format(
                    memories_text=memories_text,
                    user_message=user_message,
                    assistant_response=assistant_response,
                ),
            }
        ],
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {"facts": {"type": "array", "items": {"type": "string"}}},
                "required": ["facts"],
                "additionalProperties": False,
            },
        },
    )

    facts = json.loads(extraction.content[0].text)["facts"]
    if not facts:
        return

    print(f"Extracted: {facts}")

    # STEP 2: Consolidate - How does each fact relate to existing memories?
    for fact in facts:
        similar = user_memories.query.hybrid(
            query=fact,
            limit=10,
            filters=Filter.by_property("invalidation_time").is_none(True),
        )

        # Ask LLM: ADD, UPDATE, INVALIDATE, or NOOP?
        existing_memories = []

        for m in similar.objects:
            new_m = dict(m.properties)
            new_m["uuid"] = str(m.uuid)
            existing_memories.append(new_m)

        decision = anthropic_client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            betas=["structured-outputs-2025-11-13"],
            messages=[
                {
                    "role": "user",
                    "content": CONSOLIDATION_PROMPT_TEMPLATE.format(
                        fact=fact, existing_memories=existing_memories
                    ),
                }
            ],
            output_format={
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["ADD", "UPDATE", "INVALIDATE", "NOOP"],
                        },
                        "reasoning": {"type": "string"},
                        "target_uuid": {"type": "string"},
                        "updated_content": {"type": "string"},
                    },
                    "required": ["action", "reasoning"],
                    "additionalProperties": False,
                },
            },
        )

        action_data = json.loads(decision.content[0].text)
        action = action_data["action"]
        reasoning = action_data["reasoning"]

        # STEP 3: Execute the consolidation decision
        if action == "ADD":
            user_memories.data.insert({"content": fact})
            print(f"\n  ✓ Added: {fact}")
            print(f"    Why: {reasoning}")

        elif action == "UPDATE":
            target_uuid = action_data["target_uuid"]
            # Fetch the old memory to show what was changed
            old_memory_obj = user_memories.query.fetch_object_by_id(uuid=target_uuid)
            old_content = old_memory_obj.properties["content"]
            updated_content = action_data["updated_content"]

            user_memories.data.update(
                uuid=target_uuid,
                properties={"content": updated_content},
            )
            print(f"\n  ✓ Updated memory {target_uuid}")
            print(f"    - From: {old_content}")
            print(f"    - To:   {updated_content}")
            print(f"    - Why: {reasoning}")

        elif action == "INVALIDATE":
            target_uuid = action_data["target_uuid"]
            # Fetch the memory to show what is being invalidated.
            invalidated_memory_obj = user_memories.query.fetch_object_by_id(uuid=target_uuid)
            invalidated_content = invalidated_memory_obj.properties["content"]

            user_memories.data.update(
                uuid=target_uuid,
                properties={"invalidation_time": datetime.now(timezone.utc)},
            )
            user_memories.data.insert({"content": fact})
            print(f"\n  ✓ Invalidated memory {target_uuid}: '{invalidated_content}'")
            print(f"  ✓ Added new memory: {fact}")
            print(f"  - Why: {reasoning}")


def chat(user_id: str, message: str, memory_collection: Collection):
    """Chat with memory retrieval"""

    user_memories = memory_collection.with_tenant(user_id)

    # STEP 1: Retrieve relevant valid memories
    relevant = user_memories.query.hybrid(
        query=message,
        limit=5,
        filters=Filter.by_property("invalidation_time").is_none(True),
    )

    memories_text = "\n".join(
        [f"- {m.properties['content']}" for m in relevant.objects]
    )

    # STEP 2: Generate response with memory context
    response = anthropic_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2048,
        system="You are a helpful assistant that answers questions given the current context and memories about the user. You tend to be succint where possible, without being terse. You are still friendly and engaging, but not overly verbose. You do not always finish your responses with a question. Sometimes you just answer the question directly.",
        messages=[
            {
                "role": "user",
                "content": f"""
            Memories about the user:
            {memories_text}

            User: {message}
            Assistant:
        """,
            }
        ],
    )

    answer = response.content[0].text

    # STEP 3: Extract and consolidate new memories
    extract_and_consolidate(user_id, message, answer, memories_text, memory_collection)

    return answer


app = typer.Typer()


@app.command()
def main():
    """Main chat application"""
    with connect_to_weaviate() as db_client:
        memory_collection = get_or_create_collection(db_client)

        existing_users = list(memory_collection.tenants.get().keys())

        if not existing_users:
            user_id = questionary.text("Enter a new user ID:").ask()
            if not user_id:
                print("User ID cannot be empty. Exiting.")
                return
        else:
            login_choice = questionary.select(
                "Log in as existing user or create a new one?",
                choices=["Existing User", "New User"],
            ).ask()

            if login_choice == "Existing User":
                user_id = questionary.select(
                    "Select a user ID:", choices=existing_users
                ).ask()
            else:
                user_id = questionary.text("Enter a new user ID:").ask()
                if not user_id:
                    print("User ID cannot be empty. Exiting.")
                    return

        if user_id is None:
            # User pressed Ctrl+C
            return

        if not memory_collection.tenants.exists(user_id):
            memory_collection.tenants.create(tenants=[user_id])
            print(f"Created new user memory store for {user_id}.")
        user_memories = memory_collection.with_tenant(user_id)

        # Simple chat loop
        print(f"Logged in as {user_id}.")
        print("💬 Memory Demo (type '/' for commands, e.g., /memories, /invalidated, /quit)\n")

        while True:
            try:
                user_input = questionary.text(
                    "You: ",
                ).ask()
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                break

            if user_input is None:
                break

            if user_input[0] == "/":
                if user_input.lower().strip() == "/quit":
                    break

                elif user_input.lower().strip() == "/memories" or user_input.lower().strip() == "/invalidated":
                    if user_input.lower().strip() == "/memories":
                        filter = Filter.by_property("invalidation_time").is_none(True)
                        print("\n📝 Current memories:")
                    else:
                        filter = Filter.by_property("invalidation_time").is_none(False)
                        print("\n🗂️ Invalidated memories:")

                    retrieved_memories = user_memories.query.fetch_objects(
                        filters=filter,
                        limit=50,
                        return_metadata=MetadataQuery(
                            creation_time=True, last_update_time=True
                        ),
                    )
                    for m in retrieved_memories.objects:
                        print(f"\n  - UUID: {m.uuid}")
                        print(f"    Content: {m.properties['content']}")
                        print(f"    Created: {m.metadata.creation_time}")
                        print(f"    Updated: {m.metadata.last_update_time}")
                        if m.properties["invalidation_time"]:
                            print(f"    Invalidated: {m.properties['invalidation_time']}")

                    print()
                    continue

                else:
                    print(f"Unknown command: {user_input}")
                    continue

            response = chat(user_id, user_input, memory_collection)
            print(f"\nAssistant: {response}\n")


if __name__ == "__main__":
    app()
