import sys
from typing import Any, Dict, List, Optional, Union

# Dummy implementations of ChromaDB components

class DummyCollection:
    """A dummy implementation of ChromaDB Collection"""
    
    def __init__(self, name="dummy_collection", **kwargs):
        self.name = name
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        self.ids = []
    
    def add(self, documents=None, embeddings=None, metadatas=None, ids=None, **kwargs):
        """Store data in dummy collection"""
        if documents and ids:
            for i, doc_id in enumerate(ids):
                if doc_id not in self.ids:
                    self.ids.append(doc_id)
                    self.documents.append(documents[i] if documents else "")
                    self.metadatas.append(metadatas[i] if metadatas else {})
                    self.embeddings.append(embeddings[i] if embeddings else [0.0] * 10)
        return True
    
    def query(self, query_embeddings=None, query_texts=None, n_results=10, **kwargs):
        """Return dummy query results"""
        results = {
            "ids": [self.ids[:n_results]],
            "documents": [self.documents[:n_results]],
            "metadatas": [self.metadatas[:n_results]],
            "distances": [[0.1] * min(len(self.ids), n_results)],
            "embeddings": None
        }
        return results
    
    def get(self, **kwargs):
        """Get all documents"""
        return {
            "ids": self.ids,
            "documents": self.documents,
            "metadatas": self.metadatas,
            "embeddings": self.embeddings
        }
    
    def delete(self, ids=None, **kwargs):
        """Delete documents from collection"""
        if ids:
            for doc_id in ids:
                if doc_id in self.ids:
                    idx = self.ids.index(doc_id)
                    self.ids.pop(idx)
                    self.documents.pop(idx)
                    self.metadatas.pop(idx)
                    self.embeddings.pop(idx)
        return True

class DummyChromaDB:
    """A dummy implementation of ChromaDB client"""
    
    def __init__(self, **kwargs):
        self.collections = {}
    
    def create_collection(self, name, **kwargs):
        """Create a new collection"""
        if name not in self.collections:
            self.collections[name] = DummyCollection(name=name)
        return self.collections[name]
    
    def get_collection(self, name, **kwargs):
        """Get an existing collection"""
        if name not in self.collections:
            self.collections[name] = DummyCollection(name=name)
        return self.collections[name]
    
    def list_collections(self):
        """List all collections"""
        return list(self.collections.values())
    
    def delete_collection(self, name):
        """Delete a collection"""
        if name in self.collections:
            del self.collections[name]
        return True

def get_dummy_client(**kwargs):
    """Return a dummy ChromaDB client"""
    return DummyChromaDB(**kwargs)

def apply_dummy():
    """Replace ChromaDB with our dummy implementation"""
    try:
        # Create a dummy module
        from types import ModuleType
        
        # Create the dummy chromadb module
        chromadb_dummy = ModuleType("chromadb")
        chromadb_dummy.Client = DummyChromaDB
        chromadb_dummy.Collection = DummyCollection
        chromadb_dummy.get_client = get_dummy_client
        
        # Add QueryResult for imports in embedchain
        class QueryResult(dict):
            pass
        chromadb_dummy.QueryResult = QueryResult
        
        # Replace the real module with our dummy
        sys.modules["chromadb"] = chromadb_dummy
        
        print("Successfully replaced ChromaDB with dummy implementation")
        return True
    except Exception as e:
        print(f"Failed to install dummy ChromaDB: {str(e)}")
        return False 