"""Module for RAG implementation using Google Gemini API."""

import logging
import json
import re
import google.generativeai as genai
from .vector_database import VectorDatabaseManager
from .config import GEMINI_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class RagImplementation:
    """Class for RAG implementation using Google Gemini API."""
    
    def __init__(self, config=GEMINI_CONFIG, vector_db=None):
        """Initialize with configuration."""
        self.config = config
        self.vector_db = vector_db or VectorDatabaseManager()
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize the Gemini API client."""
        try:
            # Configure the Gemini API globally
            genai.configure(api_key=self.config['api_key'])
            # Initialize the model
            self.client = genai.GenerativeModel(self.config['model'])
            logger.info(f"Successfully initialized Gemini API with model: {self.config['model']}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            logger.warning("Proceeding without Gemini capabilities - responses will be limited")
            self.client = None
    
    def _construct_prompt(self, query, context_docs):
        """
        Construct a prompt for Gemini using the query and context documents.
        
        Args:
            query: The original query
            context_docs: List of relevant context documents
            
        Returns:
            Constructed prompt string
        """
        context_text = "\n".join([f"- {doc}" for doc in context_docs])
        
        prompt = f"""
        You are an expert social media content creator. Based on the following context from successful posts:
        
        {context_text}
        
        Generate a creative and engaging social media post about {query}.
        
        Include:
        1. An attention-grabbing caption
        2. Relevant hashtags 
        3. A call to action
        
        Output format should be JSON with the following fields:
        {{
            "caption": "Your creative caption here",
            "hashtags": ["#hashtag1", "#hashtag2"],
            "call_to_action": "Your call to action here"
        }}
        
        Ensure your response is only the JSON object, nothing else.
        """
        
        return prompt
    
    def _generate_fallback_response(self, query):
        """
        Generate a fallback response when Gemini is not available.
        
        Args:
            query: The original query
            
        Returns:
            Dictionary with fallback recommendation
        """
        try:
            # Extract topic from query
            topic = query.lower()
            
            # Generate hashtags based on topic
            hashtags = []
            if 'fashion' in topic:
                hashtags = ['#Fashion', '#Style', '#Trending']
            elif 'product' in topic:
                hashtags = ['#NewProduct', '#MustHave', '#ShopNow']
            elif 'sale' in topic or 'discount' in topic:
                hashtags = ['#Sale', '#Discount', '#LimitedOffer']
            else:
                hashtags = ['#Trending', '#MustSee', '#NewContent']
            
            # Add topic as hashtag if not already included
            topic_hashtag = f"#{topic.replace(' ', '')}"
            if topic_hashtag not in hashtags:
                hashtags.append(topic_hashtag)
            
            # Generate caption based on topic
            caption = f"Check out the latest {topic} that everyone's talking about!"
            
            # Generate call to action
            call_to_action = "Click the link in bio to learn more!"
            
            logger.info(f"Generated fallback response for query: {query}")
            
            return {
                'caption': caption,
                'hashtags': hashtags,
                'call_to_action': call_to_action
            }
        except Exception as e:
            logger.error(f"Error generating fallback response: {str(e)}")
            return {
                'caption': f"Exciting content about {query}!",
                'hashtags': ['#Trending', '#MustSee'],
                'call_to_action': "Check out our website for more!"
            }
    
    def generate_recommendation(self, query, n_context=3):
        """Generate a content recommendation based on a query."""
        try:
            # Get similar documents from vector DB
            similar_docs = self.vector_db.query_similar(query, n_results=n_context)
            
            # Check if we found any similar documents
            if similar_docs and len(similar_docs['documents'][0]) > 0:
                context_docs = similar_docs['documents'][0]
                logger.info(f"Found {len(context_docs)} similar documents for query: {query}")
            else:
                logger.warning(f"No similar documents found for query: {query}")
                # Create synthetic context based on the query
                context_docs = [
                    f"Create engaging content about {query}",
                    f"Users respond well to posts about {query} with clear calls to action",
                    f"Visual content about {query} gets high engagement"
                ]
                logger.info(f"Created synthetic context for query: {query}")
            
            # Build prompt with context
            prompt = self._construct_prompt(query, context_docs)
            
            # Generate response using Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            # Parse the response
            response_text = response.text
            
            # Clean up the response text
            response_text = response_text.strip()
            
            # Parse JSON from the response
            try:
                # Find JSON content in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    recommendation = json.loads(json_str)
                    logger.info(f"Generated recommendation for query: {query}")
                    return recommendation
                else:
                    # Try parsing the entire response as JSON
                    try:
                        recommendation = json.loads(response_text)
                        logger.info(f"Generated recommendation for query: {query}")
                        return recommendation
                    except:
                        logger.warning(f"No JSON found in response: {response_text}")
                        # Extract information from text response
                        return self._extract_recommendation_from_text(response_text, query)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from response: {str(e)}")
                logger.error(f"Response text: {response_text}")
                # Extract information from text response
                return self._extract_recommendation_from_text(response_text, query)
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            raise  # Re-raise to see the full error
    
    def apply_template(self, recommendation, template_type):
        """
        Apply a template to a recommendation.
        
        Args:
            recommendation: The recommendation to apply the template to
            template_type: The type of template to apply
            
        Returns:
            Formatted string with the template applied
        """
        from config import CONTENT_TEMPLATES
        
        try:
            template = CONTENT_TEMPLATES.get(template_type, '{caption} {hashtags}')
            
            # Format hashtags as a string
            hashtags_str = ' '.join(recommendation.get('hashtags', []))
            
            # Apply template
            formatted = template.format(
                caption=recommendation.get('caption', ''),
                hashtags=hashtags_str
            )
            
            return formatted
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return f"{recommendation.get('caption', '')} {' '.join(recommendation.get('hashtags', []))}"

    def _extract_recommendation_from_text(self, text, query):
        """Extract recommendation components from text response."""
        try:
            # Send a follow-up request to format the response as JSON
            format_prompt = f"""
            Convert the following social media post into a properly formatted JSON object:
            
            {text}
            
            Format as:
            {{
                "caption": "The main caption text",
                "hashtags": ["#hashtag1", "#hashtag2"],
                "call_to_action": "The call to action text"
            }}
            
            Return ONLY the JSON object, nothing else.
            """
            
            # Generate response using Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=format_prompt
            )
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to parse as JSON
            try:
                # Find JSON content in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    recommendation = json.loads(json_str)
                    logger.info(f"Successfully extracted recommendation from text")
                    return recommendation
                else:
                    recommendation = json.loads(response_text)
                    logger.info(f"Successfully extracted recommendation from text")
                    return recommendation
            except:
                # If all else fails, create a structured recommendation from the text
                lines = text.split('\n')
                caption = next((line for line in lines if len(line) > 20), f"Exciting content about {query}")
                
                # Extract hashtags
                hashtag_pattern = r'#\w+'
                hashtags = re.findall(hashtag_pattern, text)
                if not hashtags:
                    # Create hashtags from query
                    query_words = query.split()
                    hashtags = [f"#{word.capitalize()}" for word in query_words]
                    hashtags.append("#MustSee")
                
                # Extract call to action
                cta_candidates = [
                    line for line in lines 
                    if any(phrase in line.lower() for phrase in ["click", "check out", "visit", "learn more", "shop now", "follow"])
                ]
                call_to_action = cta_candidates[0] if cta_candidates else "Click the link in bio to learn more!"
                
                return {
                    "caption": caption,
                    "hashtags": hashtags,
                    "call_to_action": call_to_action
                }
                
        except Exception as e:
            logger.error(f"Error extracting recommendation from text: {str(e)}")
            # Create a basic recommendation based on the query
            return {
                "caption": f"Discover the latest trends in {query} that everyone's talking about!",
                "hashtags": [f"#{word.capitalize()}" for word in query.split()] + ["#TrendAlert"],
                "call_to_action": "Click the link in bio to see more!"
            }

    def generate_batch_recommendations(self, prompt, topics):
        """Generate recommendations for multiple topics in a single API call."""
        try:
            # Get context documents for all topics
            all_context = {}
            for topic in topics:
                similar_docs = self.vector_db.query_similar(topic, n_results=3)
                if similar_docs and len(similar_docs['documents'][0]) > 0:
                    all_context[topic] = similar_docs['documents'][0]
                    logger.info(f"Found {len(similar_docs['documents'][0])} similar documents for topic: {topic}")
                else:
                    # Create synthetic context
                    all_context[topic] = [
                        f"Create engaging content about {topic}",
                        f"Users respond well to posts about {topic} with clear calls to action",
                        f"Visual content about {topic} gets high engagement"
                    ]
                    logger.info(f"Created synthetic context for topic: {topic}")
            
            # Enhance the prompt with context
            enhanced_prompt = self._enhance_batch_prompt(prompt, all_context)
            
            # Generate response using Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=enhanced_prompt
            )
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to parse as JSON
            try:
                # Find JSON content in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    recommendations = json.loads(json_str)
                    logger.info(f"Successfully generated batch recommendations for {len(topics)} topics")
                    return recommendations
                else:
                    # Try parsing the entire response
                    recommendations = json.loads(response_text)
                    logger.info(f"Successfully generated batch recommendations for {len(topics)} topics")
                    return recommendations
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from batch response: {str(e)}")
                logger.error(f"Response text: {response_text}")
                # Fall back to individual recommendations
                return {}
            
        except Exception as e:
            logger.error(f"Error generating batch recommendations: {str(e)}")
            return {}
        
    def _enhance_batch_prompt(self, prompt, context_by_topic):
        """Enhance the batch prompt with context for each topic."""
        context_section = ""
        
        for topic, context_docs in context_by_topic.items():
            context_section += f"\nContext for '{topic}':\n"
            context_section += "\n".join([f"- {doc}" for doc in context_docs])
            context_section += "\n"
        
        enhanced_prompt = f"""
        {prompt}
        
        Use the following context from successful posts to inform your recommendations:
        
        {context_section}
        
        Remember to format your response as a JSON object with topics as keys.
        """
        
        return enhanced_prompt


# Test function
def test_rag_implementation():
    """Test the RAG implementation."""
    try:
        # Create vector DB manager with sample data
        vector_db = VectorDatabaseManager()
        
        # Add sample posts
        sample_posts = [
            {
                'id': '1',
                'caption': 'Summer sale going on now! #SummerSale #Discount',
                'hashtags': ['#SummerSale', '#Discount'],
                'engagement': 123
            },
            {
                'id': '2',
                'caption': 'Check out our new product line! #NewProducts',
                'hashtags': ['#NewProducts'],
                'engagement': 85
            },
            {
                'id': '3',
                'caption': 'Tips for summer fashion. #SummerStyle #Fashion',
                'hashtags': ['#SummerStyle', '#Fashion'],
                'engagement': 210
            }
        ]
        
        # Force add the sample posts
        count = vector_db.add_posts(sample_posts)
        logger.info(f"Added {count} sample posts to vector database for testing")
        
        # Verify posts were added
        collection_count = vector_db.get_count()
        logger.info(f"Vector database contains {collection_count} documents")
        
        # Create RAG implementation
        rag = RagImplementation(vector_db=vector_db)
        
        # Test recommendation generation
        query = "summer fashion trends"
        logger.info(f"Testing recommendation generation for query: {query}")
        recommendation = rag.generate_recommendation(query)
        
        # Print the recommendation for debugging
        logger.info(f"Generated recommendation: {json.dumps(recommendation, indent=2)}")
        
        # Verify if all required fields are present
        required_fields = ['caption', 'hashtags', 'call_to_action']
        has_required_fields = all(field in recommendation for field in required_fields)
        
        if has_required_fields:
            logger.info("RAG implementation test successful - all required fields present")
            return True
        else:
            missing = [field for field in required_fields if field not in recommendation]
            logger.warning(f"RAG test completed but missing required fields: {missing}")
            return False
            
    except Exception as e:
        logger.error(f"RAG implementation test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Test RAG implementation
    success = test_rag_implementation()
    print(f"RAG implementation test {'successful' if success else 'failed'}")