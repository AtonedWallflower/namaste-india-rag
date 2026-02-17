import sys
import os
# Add the project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix for Windows console encoding - ADD THIS AT THE TOP
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except AttributeError:
        # Older Python versions fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')

import chromadb
from phase2_database.embeddings import EmbeddingGenerator  # Use full path
import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_print(text):
    """Safely print text that might contain Unicode characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters
        safe_text = text.encode('ascii', 'ignore').decode('ascii')
        print(safe_text)

class VectorDatabase:
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize ChromaDB client"""
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_generator = EmbeddingGenerator()
        
        # Create or get collection
        self.collection_name = "namaste_india_tours"
        self.collection = self.get_or_create_collection()
    
    def get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(self.collection_name)
        except:
            return self.client.create_collection(self.collection_name)
    
    def load_tours_from_json(self, filepath='phase1_scraping/tour_data_cleaned.json'):
        """Load tours from JSON file - using cleaned data"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tours = json.load(f)
            logger.info(f"Loaded {len(tours)} tours from {filepath}")
            return tours
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return []
    
    def prepare_data_for_indexing(self, tours: List[Dict]) -> tuple:
        """Prepare data for ChromaDB indexing"""
        all_chunks = []
        
        for tour in tours:
            chunks = self.embedding_generator.prepare_tour_chunks(tour)
            all_chunks.extend(chunks)
        
        # Prepare IDs, embeddings, and metadata
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(all_chunks):
            # Create unique ID
            chunk_id = f"chunk_{i}_{chunk['metadata']['tour_id']}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append(chunk['metadata'])
        
        return ids, documents, metadatas
    
    def index_tours(self, tours: List[Dict]):
        """Index tours in the vector database"""
        if not tours:
            logger.warning("No tours to index")
            return
        
        # Prepare data
        ids, documents, metadatas = self.prepare_data_for_indexing(tours)
        
        # Generate embeddings
        logger.info("Generating embeddings for chunks...")
        embeddings = self.embedding_generator.generate_embeddings(documents)
        
        # Add to collection
        logger.info(f"Adding {len(documents)} chunks to database...")
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully indexed {len(documents)} chunks")
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar chunks"""
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embeddings([query])
        
        # Search
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        return results
    
    def get_context_for_query(self, query: str, n_results: int = 3) -> str:
        """Get context from database for a query"""
        results = self.search(query, n_results)
        
        if not results['documents']:
            return ""
        
        # Combine documents into context
        context_parts = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            context_parts.append(f"[From {metadata.get('tour_name', 'Unknown Tour')}]: {doc}")
        
        return "\n\n".join(context_parts)

def clean_text_for_display(text, max_length=200):
    """Clean text for safe display in console"""
    if not text:
        return ""
    
    # Replace problematic characters
    text = text.replace('➝', '->').replace('→', '->').replace('•', '-')
    
    # Remove other potential problematic characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def main():
    """Main function to run the indexing process"""
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Load tours from cleaned file
    tours = vector_db.load_tours_from_json('phase1_scraping/tour_data_cleaned.json')
    
    if tours:
        # Index tours
        vector_db.index_tours(tours)
        
        # Test search
        test_queries = [
            "pilgrimage tours in Uttarakhand",
            "Rajasthan heritage tours with forts",
            "yoga and meditation packages",
            "tours that include Agra and Jaipur",
            "beach destinations in India"
        ]
        
        print("\n" + "="*50)
        print("TESTING SEARCH RESULTS")
        print("="*50)
        
        for query in test_queries:
            print(f"\n Query: {query}")
            results = vector_db.search(query, n_results=2)
            
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    # Clean the text for display
                    clean_doc = clean_text_for_display(doc)
                    print(f"\n  Result {i+1}:")
                    # Use safe_print to handle any remaining issues
                    safe_print(f"  {clean_doc}")
            else:
                print("  No results found")
            print("-"*50)
    else:
        print("No tours found to index. Please run the cleaner first.")

if __name__ == "__main__":
    main()