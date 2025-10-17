from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def initialize_pinecone():
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable not set")

    pc = Pinecone(api_key = PINECONE_API_KEY)
    index_name = "notebooklm-index"

    if not pc.has_index(index_name):
        pc.create_index(
            name = index_name,
            dimension = 768,
            metric = "cosine",
            spec = ServerlessSpec(cloud="aws", region="us-east-1")
        )

    return pc.Index(index_name)