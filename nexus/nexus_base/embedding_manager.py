from dotenv import load_dotenv
from openai import OpenAI

load_dotenv


class EmbeddingManager:
    def __init__(self):
        try:
            self.client = OpenAI()
            self.model = "text-embedding-3-small"
        except Exception as e:
            raise Exception(f"Error loading OpenAI client for Embedding: {e}")

    def get_embedding(self, text):
        if text is None:
            return None
        text = str(text)
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=self.model)
            .data[0]
            .embedding
        )
