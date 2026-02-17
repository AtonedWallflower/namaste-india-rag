from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Initialize the embedding model"""
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            return np.array([])
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def prepare_tour_chunks(self, tour: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break tour data into chunks for embedding"""
        chunks = []
        
        # Create main description chunk
        main_text = f"Tour Name: {tour.get('name', '')}\n"
        main_text += f"Duration: {tour.get('duration', '')}\n"
        main_text += f"Theme: {tour.get('theme', '')}\n"
        main_text += f"Destinations: {', '.join(tour.get('destinations', []))}\n"
        main_text += f"Price: {tour.get('price', '')}"
        
        chunks.append({
            'text': main_text,
            'metadata': {
                'tour_name': tour.get('name', ''),
                'chunk_type': 'main_info',
                'tour_id': hash(tour.get('name', '')) % 10000
            }
        })
        
        # Create highlights chunks
        highlights = tour.get('highlights', [])
        for i, highlight in enumerate(highlights):
            if highlight:  # Only if not empty
                chunks.append({
                    'text': f"Tour: {tour.get('name', '')} - Highlight: {highlight}",
                    'metadata': {
                        'tour_name': tour.get('name', ''),
                        'chunk_type': 'highlight',
                        'highlight_index': i,
                        'tour_id': hash(tour.get('name', '')) % 10000
                    }
                })
        
        return chunks