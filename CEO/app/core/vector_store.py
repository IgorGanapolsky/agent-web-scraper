#!/usr/bin/env python3
"""
Vector Store Manager for Agentic RAG System
Handles ChromaDB integration and document management
"""

import asyncio
from pathlib import Path
from typing import Any

import chromadb
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore


class VectorStoreManager:
    """Manages vector stores and indices for the agentic RAG system"""

    def __init__(self, persist_dir: str = "data/vector_stores"):
        """Initialize the vector store manager"""

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir / "chroma")
        )

        # Track active collections and indices
        self.collections: dict[str, Any] = {}
        self.vector_stores: dict[str, ChromaVectorStore] = {}

        print(f"🗄️ Vector Store Manager initialized at {self.persist_dir}")

    async def index_exists(self, index_name: str) -> bool:
        """Check if an index already exists"""

        try:
            collection = self.chroma_client.get_collection(name=index_name)
            return collection.count() > 0
        except Exception:
            return False

    async def create_index(
        self, index_name: str, documents: list[Document]
    ) -> VectorStoreIndex:
        """Create a new vector index from documents"""

        print(f"🔧 Creating new index: {index_name}")

        # Create or get ChromaDB collection
        collection = self.chroma_client.get_or_create_collection(
            name=index_name,
            metadata={"description": f"Vector collection for {index_name}"},
        )

        # Create ChromaVectorStore
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create and persist index
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True,
        )

        # Store references
        self.collections[index_name] = collection
        self.vector_stores[index_name] = vector_store

        print(f"✅ Index created: {index_name} with {len(documents)} documents")
        return index

    async def load_index(self, index_name: str) -> VectorStoreIndex:
        """Load an existing vector index"""

        print(f"📂 Loading existing index: {index_name}")

        # Get existing collection
        collection = self.chroma_client.get_collection(name=index_name)

        # Create vector store from existing collection
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load index
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
        )

        # Store references
        self.collections[index_name] = collection
        self.vector_stores[index_name] = vector_store

        document_count = collection.count()
        print(f"✅ Index loaded: {index_name} with {document_count} documents")
        return index

    async def add_documents(self, index_name: str, documents: list[Document]) -> None:
        """Add documents to an existing index"""

        if index_name not in self.vector_stores:
            raise ValueError(f"Vector store {index_name} not found")

        print(f"📝 Adding {len(documents)} documents to {index_name}")

        # Get vector store and create temporary index for new documents
        vector_store = self.vector_stores[index_name]
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Add documents to existing vector store
        for doc in documents:
            # Create temporary index to insert the document
            VectorStoreIndex.from_documents(
                [doc],
                storage_context=storage_context,
            )

        print(f"✅ Documents added to {index_name}")

    async def delete_index(self, index_name: str) -> None:
        """Delete an entire index"""

        try:
            self.chroma_client.delete_collection(name=index_name)

            # Clean up references
            if index_name in self.collections:
                del self.collections[index_name]
            if index_name in self.vector_stores:
                del self.vector_stores[index_name]

            print(f"🗑️ Index deleted: {index_name}")

        except Exception as e:
            print(f"❌ Error deleting index {index_name}: {e}")

    async def list_indices(self) -> list[str]:
        """List all available indices"""

        collections = self.chroma_client.list_collections()
        return [collection.name for collection in collections]

    async def get_index_stats(self, index_name: str) -> dict[str, Any]:
        """Get statistics for a specific index"""

        try:
            collection = self.chroma_client.get_collection(name=index_name)

            stats = {
                "name": index_name,
                "document_count": collection.count(),
                "metadata": collection.metadata,
            }

            return stats

        except Exception as e:
            return {"error": f"Could not get stats for {index_name}: {e}"}

    async def search_documents(
        self, index_name: str, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Search documents in a specific index"""

        if index_name not in self.collections:
            raise ValueError(f"Collection {index_name} not found")

        collection = self.collections[index_name]

        # Perform similarity search
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append(
                {
                    "document": results["documents"][0][i],
                    "metadata": (
                        results["metadatas"][0][i] if results["metadatas"][0] else {}
                    ),
                    "distance": (
                        results["distances"][0][i] if results["distances"][0] else 0.0
                    ),
                }
            )

        return formatted_results

    async def backup_index(self, index_name: str, backup_path: str) -> None:
        """Backup an index to a specified path"""

        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Export collection data
        if index_name in self.collections:
            collection = self.collections[index_name]

            # Get all documents
            results = collection.get(include=["documents", "metadatas", "embeddings"])

            # Save to backup file
            import json

            backup_file = backup_dir / f"{index_name}_backup.json"

            backup_data = {
                "name": index_name,
                "metadata": collection.metadata,
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "ids": results.get("ids", []),
            }

            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=2)

            print(f"💾 Index backed up: {index_name} -> {backup_file}")

    async def restore_index(self, backup_path: str) -> str:
        """Restore an index from backup"""

        import json

        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        with open(backup_file) as f:
            backup_data = json.load(f)

        index_name = backup_data["name"]
        documents = backup_data["documents"]
        metadatas = backup_data.get("metadatas", [])

        # Convert to LlamaIndex documents
        doc_objects = []
        for i, doc_text in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            doc_objects.append(Document(text=doc_text, metadata=metadata))

        # Create index
        await self.create_index(index_name, doc_objects)

        print(f"📥 Index restored: {index_name} from {backup_file}")
        return index_name

    async def optimize_index(self, index_name: str) -> None:
        """Optimize an index for better performance"""

        # ChromaDB handles optimization internally
        # This is a placeholder for future optimization strategies
        print(f"🔧 Optimizing index: {index_name}")

        if index_name in self.collections:
            collection = self.collections[index_name]
            doc_count = collection.count()
            print(f"✅ Index optimized: {index_name} ({doc_count} documents)")

    def get_storage_info(self) -> dict[str, Any]:
        """Get storage information and usage statistics"""

        storage_info = {
            "persist_directory": str(self.persist_dir),
            "total_indices": len(self.collections),
            "indices": {},
        }

        for name, collection in self.collections.items():
            storage_info["indices"][name] = {
                "document_count": collection.count(),
                "metadata": collection.metadata,
            }

        return storage_info

    async def cleanup_storage(self) -> None:
        """Clean up storage and remove temporary files"""

        print("🧹 Cleaning up vector storage...")

        # ChromaDB handles cleanup internally
        # Additional cleanup logic can be added here

        print("✅ Storage cleanup complete")


async def main():
    """Test the vector store manager"""

    print("🧪 Testing Vector Store Manager")

    manager = VectorStoreManager()

    # Create test documents
    test_docs = [
        Document(
            text="Python automation tools are in high demand for SaaS startups",
            metadata={"source": "reddit", "topic": "automation"},
        ),
        Document(
            text="SMB businesses struggle with manual data entry processes",
            metadata={"source": "reddit", "topic": "pain_points"},
        ),
    ]

    # Test index creation
    index_name = "test_index"
    await manager.create_index(index_name, test_docs)

    # Test search
    results = await manager.search_documents(index_name, "Python automation", top_k=2)
    print(f"Search results: {len(results)} documents found")

    # Test stats
    stats = await manager.get_index_stats(index_name)
    print(f"Index stats: {stats}")

    # Test storage info
    storage_info = manager.get_storage_info()
    print(f"Storage info: {storage_info}")

    # Cleanup
    await manager.delete_index(index_name)
    print("✅ Test complete")


if __name__ == "__main__":
    asyncio.run(main())
