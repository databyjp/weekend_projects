from basic import connect_to_weaviate


with connect_to_weaviate() as db_client:
    db_client.collections.delete("Memory")
