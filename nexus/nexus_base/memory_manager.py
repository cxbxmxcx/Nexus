import json

import chromadb
import pandas as pd
from dotenv import load_dotenv
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

from nexus.nexus_base.embedding_manager import EmbeddingManager
from nexus.nexus_base.nexus_models import MemoryStore, MemoryType, db
from nexus.nexus_base.utils import (
    convert_keys_to_lowercase,
    extract_code,
    id_hash,
)

load_dotenv()


class MemoryManager:
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.CHROMA_DB = "nexus_memory_chroma_db"
        self.initialize_stores()

    def initialize_stores(self):
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collections = chroma_client.list_collections()
        for collection in collections:
            self.add_memory_store(collection.name)

    def add_memory_store(self, store_name):
        if store_name is None or store_name == "None":
            return False
        with db.atomic():
            if MemoryStore.select().where(MemoryStore.name == store_name).count() == 0:
                MemoryStore.create(name=store_name)
                return True
        return False

    def get_memory_embedding(self, text):
        return self.embedding_manager.get_embedding(text)

    def query_memories(self, memory_store_name, input_text, n_results=5):
        if memory_store_name is None or input_text is None:
            return None

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store_name)
        embedding = self.get_memory_embedding(input_text)
        docs = collection.query(
            query_embeddings=[embedding], n_results=n_results, include=["documents"]
        )
        return docs["documents"]

    def apply_memory_RAG(
        self, memory_store, memory_function, input_text, agent, n_results=5
    ):
        if memory_store is None or input_text is None:
            return None

        # basic form of memory
        if memory_store.memory_type == MemoryType.CONVERSATIONAL.value:
            docs = self.query_memories(memory_store.name, input_text, n_results)

            prompt = ""
            if docs:
                prompt += "\nUse the following memories to help answer the question:\n"
                for i, doc in enumerate(docs):
                    prompt += f"Memory {i+1}:\n{doc}\n"
            return prompt
        else:
            # semantic form of memory
            semantics = agent.get_semantic_response(
                memory_function.augmentation_prompt, input_text
            )
            semantics, code = extract_code(semantics)
            if code:
                semantics = code[0][1]
            semantics = json.loads(semantics)
            semantics = convert_keys_to_lowercase(semantics)
            semantics = sum(
                [
                    semantics[key.lower()]
                    for key in memory_function.augmentation_keys.split(",")
                ],
                [],
            )

            memories = []
            for semantic in semantics:
                docs = self.query_memories(memory_store.name, semantic, n_results)
                memories.extend(docs)

            prompt = f"\nThe following memories are specific to {memory_function.augmentation_keys} and may help provide additional context:\n"
            for memory in memories:
                prompt += f"Memory:\n{memory}\n"

            return prompt

    def get_memories(self, memory_store, include=["documents", "embeddings"]):
        if memory_store is None:
            return None
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store)
        memories = collection.get(include=include)
        return memories

    def get_splitter(self, memory_store):
        chunking_option = memory_store.chunking_option
        chunk_size = memory_store.chunk_size
        overlap = memory_store.overlap

        if chunking_option == "Character":
            return CharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=overlap, separator="\n"
            )
        elif chunking_option == "Recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False,
            )

    def examine_memories(self, memory_store):
        """
        Displays all documents from ChromaDB.
        """
        if memory_store is None:
            return None
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store)
        memories = collection.get(include=["documents"])

        df = pd.DataFrame({"ID Hash": memories["ids"], "Memory": memories["documents"]})

        # Display the DataFrame in Streamlit
        return df

    def delete_memory_store(self, memory_store):
        if memory_store is None:
            return False
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        chroma_client.delete_collection(memory_store)
        return True

    def append_memory(
        self, memory_store, user_input, llm_response, memory_function=None, agent=None
    ):
        if (
            memory_store is None
            or user_input is None
            or agent is None
            or memory_function is None
        ):
            return False

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store.name)

        if llm_response is None:
            memory = f"""            
            {user_input}
            """
        else:
            memory = f"""
            user:
            {user_input}
            assistant:
            {llm_response}
            """

        try:
            memories = agent.get_semantic_response(
                memory_function.function_prompt, memory
            )
            memories, code = extract_code(memories)
            if code:
                memories = code[0][1]
            memories = json.loads(memories)
            memories = convert_keys_to_lowercase(memories)
            memories = sum(
                [
                    memories[key.lower()]
                    for key in memory_function.function_keys.split(",")
                ],
                [],
            )

            for memory in memories:
                embedding = self.get_memory_embedding(memory)
                id = id_hash(memory)
                docs = collection.get(ids=[id], include=["documents"])["documents"]
                if docs is None or len(docs) == 0:
                    collection.add(embeddings=[embedding], documents=[memory], ids=[id])

            return True
        except Exception as e:
            print("Error appending memory: ", e)
            return False

    def compress_memories(
        self, memory_store, grouped_memories, memory_function, chat_agent
    ):
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        chroma_client.delete_collection(memory_store.name)
        collection = chroma_client.get_or_create_collection(name=memory_store.name)

        for key, items in grouped_memories.items():
            try:
                # 1. create a list of memories
                items = "\n".join(items)

                # 2. get the semantic response asking to summarize the memories
                summarized_memories = chat_agent.get_semantic_response(
                    memory_function.summarization_prompt, items
                )

                # 3. get the semantic response asking to extract new memories
                memories = chat_agent.get_semantic_response(
                    memory_function.function_prompt, summarized_memories
                )
                memories, code = extract_code(memories)
                if code:
                    memories = code[0][1]
                memories = json.loads(memories)
                memories = convert_keys_to_lowercase(memories)
                memories = sum(
                    [
                        memories[key.lower()]
                        for key in memory_function.function_keys.split(",")
                    ],
                    [],
                )
                # 4. add the new memories to the collection
                for memory in memories:
                    embedding = self.get_memory_embedding(memory)
                    id = id_hash(memory)
                    docs = collection.get(ids=[id], include=["documents"])["documents"]
                    if docs is None or len(docs) == 0:
                        collection.add(
                            embeddings=[embedding], documents=[memory], ids=[id]
                        )
            except Exception as e:
                print("Error compressing memories: ", e)
