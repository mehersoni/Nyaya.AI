# graphrag/engine.py

from knowledge_graph.loader import KnowledgeGraphLoader
from query_engine.retriever import GraphRetriever
from query_engine.context_builder import ContextBuilder

class GraphRAGEngine:
    def __init__(self):
        self.graph = KnowledgeGraphLoader().load()
        self.retriever = GraphRetriever(self.graph)
        self.context_builder = ContextBuilder(self.graph)
