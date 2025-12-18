"""Agent with RAG search."""

import asyncio

from examples.rag.rag_pipeline import DOC_PATH, QUESTION
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.roles import Sales
from llama_index.embeddings.zhipuai import ZhipuAIEmbedding
from metagpt.rag.schema import BM25RetrieverConfig
embedding = ZhipuAIEmbedding(model="embedding-2", api_key="3114a609d68448efb5d459ee5b7e10da.3fbNyLNPdeOtoJbF")

path="/Users/ash/Desktop/毕业/MetaGPT/examples/data/rag"
ques = "现在什么是玩具行业新风潮"

async def search():
    """Agent with RAG search."""
    store = SimpleEngine.from_docs(input_dir=path,embed_model = embedding,retriever_configs=[BM25RetrieverConfig()])
    role = Sales(profile="Sales", store=store)
    result = await role.run(ques)

if __name__ == "__main__":
    asyncio.run(search())
