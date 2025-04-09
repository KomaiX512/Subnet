"""Module for vector database operations using a simpler embedding approach."""

import logging
import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .config import VECTOR_DB_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class VectorDatabaseManager:
    """Class to handle vector database operations."""
    
    def __init__(self, config=VECTOR_DB_CONFIG):
        """Initialize with vector database configuration."""
        self.config = config
        self.client = chromadb.Client()
        self.collection = self._get_or_create_collection()
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer()
        self.fitted = False
        
    def _get_or_create_collection(self):
        """Get or create a collection in the vector database."""
        try:
            collection = self.client.get_or_create_collection(
                name=self.config['collection_name']
            )
            logger.info(f"Using collection: {self.config['collection_name']}")
            return collection
        except Exception as e:
            logger.error(f"Error with collection: {str(e)}")
            raise
    
    def _get_embeddings(self, texts):
        """Generate embeddings for the given texts using TF-IDF."""
        try:
            if not self.fitted:
                # First time, fit and transform
                embeddings = self.vectorizer.fit_transform(texts).toarray()
                self.fitted = True
            else:
                # For subsequent calls, just transform
                embeddings = self.vectorizer.transform(texts).toarray()
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            normalized_embeddings = embeddings / norms
            
            return normalized_embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def add_documents(self, documents, ids=None, metadatas=None):
        """Add documents to the vector database."""
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            embeddings = self._get_embeddings(documents)
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to the collection")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def query_similar(self, query_text, n_results=5):
        """Query for similar documents."""
        try:
            query_embedding = self._get_embeddings([query_text])[0]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            logger.info(f"Found {len(results['documents'][0])} similar documents")
            return results
        except Exception as e:
            logger.error(f"Error querying similar documents: {str(e)}")
            raise
    
    def get_count(self):
        """Get the number of documents in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0
    
    def add_posts(self, posts):
        """Add social media posts to the vector database."""
        try:
            documents = []
            ids = []
            metadatas = []
            
            for post in posts:
                # Extract text content
                text = post.get('caption', '')
                
                # Skip empty posts
                if not text:
                    continue
                
                # Add to lists
                documents.append(text)
                ids.append(f"post_{post.get('id', len(documents))}")
                
                # Extract metadata - convert any lists to strings to avoid ChromaDB errors
                metadata = {
                    'engagement': int(post.get('engagement', 0)),
                    'likes': int(post.get('likes', 0)),
                    'comments': int(post.get('comments', 0)),
                    'timestamp': str(post.get('timestamp', ''))
                }
                
                # Add hashtags if available - convert list to string
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        metadata['hashtags'] = ' '.join(post['hashtags'])
                    else:
                        metadata['hashtags'] = str(post['hashtags'])
                
                metadatas.append(metadata)
            
            # Add to collection
            if documents:
                self.add_documents(documents, ids, metadatas)
                return len(documents)
            else:
                logger.warning("No valid posts to add")
                return 0
                
        except Exception as e:
            logger.error(f"Error adding posts: {str(e)}")
            return 0
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Get current count
            count_before = self.get_count()
            
            # Delete collection and recreate it
            self.client.delete_collection(self.config['collection_name'])
            self.collection = self._get_or_create_collection()
            
            # Reset vectorizer
            self.vectorizer = TfidfVectorizer()
            self.fitted = False
            
            logger.info(f"Cleared collection with {count_before} documents")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False

# Function to test the vector database
def test_vector_db():
    """Test vector database operations."""
    try:
        manager = VectorDatabaseManager()
        
        # Test documents
        test_docs = [
            "Engagement is high for posts about product features",
            "Users respond well to promotional content with discounts",
            "Tutorial videos get the most shares and comments",
            "Behind-the-scenes content builds brand loyalty"
        ]
        
        # Test adding documents
        manager.add_documents(
            documents=test_docs,
            ids=["doc_1", "doc_2", "doc_3", "doc_4"],
            metadatas=[
                {"type": "feature", "engagement": 0.8},
                {"type": "promotion", "engagement": 0.7},
                {"type": "tutorial", "engagement": 0.9},
                {"type": "brand", "engagement": 0.6}
            ]
        )
        
        # Test querying
        query = "What content gets the most engagement?"
        results = manager.query_similar(query)
        
        print("\nQuery:", query)
        print("\nResults:")
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            print(f"- {doc} (Type: {metadata.get('type', 'N/A')}, Engagement: {metadata.get('engagement', 'N/A')})")
        
        return True
    except Exception as e:
        logger.error(f"Vector database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the vector database
    success = test_vector_db()
    print(f"\nVector database test {'successful' if success else 'failed'}")