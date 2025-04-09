"""Main module for the social media content recommendation system."""

import logging
import json
import os
import io
from datetime import datetime
from template.base.utils.data_retrieval import R2DataRetriever
from template.base.utils.time_series_analysis import TimeSeriesAnalyzer
from template.base.utils.vector_database import VectorDatabaseManager
from template.base.utils.rag_implementation import RagImplementation
from template.base.utils.recommendation_generation import RecommendationGenerator
from template.base.utils.config import R2_CONFIG, LOGGING_CONFIG, GEMINI_CONFIG
import pandas as pd
from template.base.utils.r2_storage_manager import R2StorageManager
from template.base.utils.instagram_scraper import InstagramScraper

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class ContentRecommendationSystem:
    """Class for the complete content recommendation system."""
    
    def __init__(self):
        """Initialize all components of the system."""
        logger.info("Initializing Content Recommendation System")
        
        # Initialize components
        self.data_retriever = R2DataRetriever()
        self.vector_db = VectorDatabaseManager()
        self.time_series = TimeSeriesAnalyzer()
        self.rag = RagImplementation(vector_db=self.vector_db)
        self.recommendation_generator = RecommendationGenerator(
            rag=self.rag,
            time_series=self.time_series
        )
        # Initialize R2 Storage Manager (for exporting to the tasks bucket)
        self.storage_manager = R2StorageManager()
    
    def ensure_sample_data_in_r2(self):
        """
        Ensure that sample data exists in the R2 bucket.
        This is a stub implementation. Add your logic here if needed.
        """
        logger.info("ensure_sample_data_in_r2: Stub implementation; no sample data was uploaded.")
        return True

    def process_social_data(self, data_key):
        """
        Process social media data from R2.
        
        Args:
            data_key: Key of the data file in R2
            
        Returns:
            Dictionary with processed data or None if processing fails
        """
        try:
            logger.info(f"Processing social data from {data_key}")
            
            # Get data from R2
            raw_data = self.data_retriever.get_json_data(data_key)
            
            # Check if we have data
            if raw_data is None:  # Explicitly check for None
                logger.error(f"No data found at {data_key}")
                return None
            
            # Case 1: Raw Instagram data coming as a list with a 'latestPosts' key in first element
            if isinstance(raw_data, list) and raw_data and 'latestPosts' in raw_data[0]:
                data = self.process_instagram_data(raw_data)
                if data:
                    logger.info("Successfully processed Instagram data")
                    return data
                else:
                    logger.error("Failed to process Instagram data")
                    return None
            
            # Case 2: Already processed data (a dictionary with required keys)
            elif isinstance(raw_data, dict) and 'posts' in raw_data and 'engagement_history' in raw_data:
                logger.info("Data is already processed. Using it directly.")
                return raw_data
            
            else:
                logger.error(f"Unsupported data format in {data_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing social data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def process_instagram_data(self, raw_data):
        """
        Process Instagram data format into the expected structure.
        
        Args:
            raw_data: Raw Instagram JSON data
            
        Returns:
            Dictionary with processed data in the expected format
        """
        try:
            # Check if data is in the expected Instagram format
            if not isinstance(raw_data, list) or not raw_data:
                logger.warning("Invalid Instagram data format")
                return None
            
            # Extract account data
            account_data = raw_data[0]
            
            # Debug the structure
            logger.info(f"Instagram data keys: {list(account_data.keys())}")
            
            # Extract posts from latestPosts field
            posts = []
            engagement_history = []
            
            # Check if latestPosts exists in the account data
            if 'latestPosts' in account_data and isinstance(account_data['latestPosts'], list):
                instagram_posts = account_data['latestPosts']
                logger.info(f"Found {len(instagram_posts)} posts in latestPosts")
                
                for post in instagram_posts:
                    # Some posts might have childPosts (carousel posts)
                    if 'childPosts' in post and post['childPosts']:
                        logger.info(f"Post {post.get('id', '')} has {len(post['childPosts'])} child posts")
                    
                    # Create post object with required fields
                    post_obj = {
                        'id': post.get('id', ''),
                        'caption': post.get('caption', ''),
                        'hashtags': post.get('hashtags', []),
                        'engagement': 0,  # Will calculate below
                        'likes': 0,
                        'comments': post.get('commentsCount', 0),
                        'timestamp': post.get('timestamp', ''),
                        'url': post.get('url', ''),
                        'type': post.get('type', '')
                    }
                    
                    # Handle likes which might be null
                    if post.get('likesCount') is not None:
                        post_obj['likes'] = post['likesCount']
                        
                    # Calculate engagement
                    post_obj['engagement'] = post_obj['likes'] + post_obj['comments']
                    
                    # Only add posts with captions
                    if post_obj['caption']:
                        posts.append(post_obj)
                        
                        # Add to engagement history if timestamp exists
                        if post.get('timestamp'):
                            engagement_record = {
                                'timestamp': post.get('timestamp'),
                                'engagement': post_obj['engagement']
                            }
                            engagement_history.append(engagement_record)
            
            # Log post count for debugging
            logger.info(f"Processed {len(posts)} posts from Instagram data")
            
            # If no posts were processed, handle this case
            if not posts:
                logger.warning("No posts extracted from Instagram data")
                # Create synthetic timestamps and engagement if needed for time series
                now = datetime.now()
                for i in range(3):
                    timestamp = (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    engagement = 1000 - (i * 100)  # Decreasing engagement
                    engagement_history.append({
                        'timestamp': timestamp,
                        'engagement': engagement
                    })
                logger.info(f"Created {len(engagement_history)} synthetic engagement records for time series")
            
            # Sort engagement history by timestamp
            engagement_history.sort(key=lambda x: x['timestamp'])
            
            # Create processed data structure
            processed_data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': {
                    'username': account_data.get('username', ''),
                    'fullName': account_data.get('fullName', ''),
                    'followersCount': account_data.get('followersCount', 0),
                    'followsCount': account_data.get('followsCount', 0),
                    'biography': account_data.get('biography', ''),
                    'account_type': account_data.get('account_type', 'unknown')
                }
            }
            
            return processed_data
        
        except Exception as e:
            logger.error(f"Error processing Instagram data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def index_posts(self, posts):
        """
        Index posts in the vector database.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Number of posts indexed
        """
        try:
            logger.info(f"Indexing {len(posts)} posts")
            
            # Add posts to vector DB
            count = self.vector_db.add_posts(posts)
            
            logger.info(f"Successfully indexed {count} posts")
            return count
            
        except Exception as e:
            logger.error(f"Error indexing posts: {str(e)}")
            return 0
    
    def analyze_engagement(self, data):
        """
        Analyze engagement data.
        
        Args:
            data: Dictionary with engagement data
            
        Returns:
            Analysis results
        """
        try:
            logger.info("Analyzing engagement data")
            
            # Prepare engagement data
            if not data or not data.get('engagement_history'):
                logger.warning("No engagement data found")
                return None
            
            engagement_data = data['engagement_history']
            
            # Analyze with time series
            results = self.time_series.analyze_data(
                engagement_data,
                timestamp_col='timestamp',
                value_col='engagement'
            )
            
            logger.info("Successfully analyzed engagement data")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return None
    
    def generate_content_plan(self, topics=None, n_recommendations=3):
        """
        Generate a content plan for given topics.
        
        Args:
            topics: List of topics (if None, detect trending)
            n_recommendations: Number of recommendations per topic
            
        Returns:
            Dictionary with content plan
        """
        try:
            logger.info("Generating content plan")
            
            # If no topics provided, use trending topics
            if not topics:
                data = self.process_social_data()
                if data and data.get('engagement_history'):
                    trending = self.recommendation_generator.generate_trending_topics(
                        data['engagement_history'],
                        top_n=3
                    )
                    topics = [trend['topic'] for trend in trending]
                
                # Fallback topics if no trending detected
                if not topics:
                    topics = ["summer fashion", "product promotion", "customer engagement"]
            
            # Generate recommendations
            recommendations = self.recommendation_generator.generate_recommendations(
                topics,
                n_recommendations=n_recommendations
            )
            
            # Create content plan
            content_plan = {
                'generated_date': datetime.now().strftime('%Y-%m-%d'),
                'topics': topics,
                'recommendations': recommendations
            }
            
            logger.info(f"Successfully generated content plan with {len(topics)} topics")
            return content_plan
            
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            return None
    
    def save_content_plan(self, content_plan, filename='content_plan.json'):
        """
        Save content plan to a file.
        
        Args:
            content_plan: Dictionary with content plan
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Saving content plan to {filename}")
            
            with open(filename, 'w') as f:
                json.dump(content_plan, f, indent=2)
            
            logger.info(f"Successfully saved content plan to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving content plan: {str(e)}")
            return False

    def export_content_plan_sections(self, content_plan):
        """Export content plan sections to R2 with username-based directory structure"""
        try:
            logger.info("Starting content plan export")
            
            if not content_plan:
                logger.error("Cannot export empty content plan")
                return False

            # Extract username from the processed data
            username = content_plan.get('profile_analysis', {}).get('username')
            if not username:
                logger.error("Cannot export - username not found in content plan")
                return False

            # Validate required sections
            required_sections = {
                'recommendations': ['profile_analysis', 'improvement_recommendations', 'competitors'],
                'creative': ['next_post_prediction']
            }
            
            # Prepare recommendations export
            recommendations = {
                section: content_plan.get(section, {})
                for section in required_sections['recommendations']
            }
            
            # Prepare creative export
            creative = content_plan.get('next_post_prediction', {})
            if not creative.get('image_prompt') or not creative.get('caption'):
                logger.warning("Incomplete creative section in content plan")

            # Create file objects
            recommendations_file = io.BytesIO(
                json.dumps(recommendations, indent=2).encode('utf-8')
            )
            creative_file = io.BytesIO(
                json.dumps(creative, indent=2).encode('utf-8')
            )

            # Export paths with username-based directory structure
            export_paths = {
                'recommendations': {
                    'key': f'recommendations/{username}/content_analysis.json',
                    'file': recommendations_file
                },
                'creative': {
                    'key': f'next_post/{username}/next_post_prediction.json',
                    'file': creative_file
                }
            }

            # Execute exports
            results = {}
            for section, data in export_paths.items():
                success = self.storage_manager.upload_file(
                    key=data['key'],
                    file_obj=data['file'],
                    bucket='tasks'
                )
                results[section] = success
                if not success:
                    logger.error(f"Failed to export {section} section")

            # Verify all exports succeeded
            if all(results.values()):
                logger.info("All content plan sections exported successfully")
                return True
            
            logger.error(f"Partial export failure: {[k for k,v in results.items() if not v]}")
            return False

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return False

    def run_pipeline(self, object_key):
        """Run the complete pipeline for content recommendation."""
        try:
            logger.info("Starting pipeline")
            
            # Step 1: Retrieve and process data
            data = self.process_social_data(object_key)
            
            if not data or not data.get('posts'):
                logger.info(f"No posts found in {object_key}, checking account type...")
                account_type = data.get('profile', {}).get('account_type', 'unknown')
                
                if account_type == 'business_no_posts':
                    logger.info("Generating initial content suggestions for business account")
                    return self.handle_new_business_account(data)
                elif account_type == 'private_account':
                    logger.warning("Skipping private account analysis")
                    return {"success": False, "message": "Private account cannot be analyzed"}
                # ... other account type handling
                
            # Step 2: Index posts
            posts_indexed = self.index_posts(data['posts'])
            if posts_indexed == 0:
                logger.error("Pipeline failed: No posts indexed")
                return {
                    "success": False,
                    "data_retrieved": True,
                    "posts_indexed": 0,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }
            
            # Step 3: Analyze engagement
            engagement_analysis = self.analyze_engagement(data)
            if engagement_analysis is None:
                logger.error("Pipeline failed: Engagement analysis failed")
                return {
                    "success": False,
                    "data_retrieved": True,
                    "posts_indexed": posts_indexed,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }
            
            # Step 4: Generate content plan
            content_plan = self.recommendation_generator.generate_content_plan(data)
            if content_plan is None:
                logger.error("Pipeline failed: Content plan generation failed")
                return {
                    "success": False,
                    "data_retrieved": True,
                    "posts_indexed": posts_indexed,
                    "engagement_analyzed": True,
                    "plan_generated": False,
                    "plan_saved": False
                }
            
            # Step 5: Save content plan
            plan_saved = self.save_content_plan(content_plan)
            if not plan_saved:
                logger.error("Pipeline failed: Content plan save failed")
                return {
                    "success": False,
                    "data_retrieved": True,
                    "posts_indexed": posts_indexed,
                    "engagement_analyzed": True,
                    "plan_generated": True,
                    "plan_saved": False
                }
            
            # Step 6: Export content plan sections
            exported = self.export_content_plan_sections(content_plan)
            
            logger.info("Pipeline completed successfully")
            return {
                "success": True,
                "message": "Content plan generated successfully",
                "data_retrieved": True,
                "posts_indexed": posts_indexed,
                "engagement_analyzed": True,
                "plan_generated": True,
                "plan_saved": True,
                "exported_plan_sections": exported,
                "content_plan": content_plan
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            return {"success": False, "message": str(e)}

    def handle_new_business_account(self, data):
        """Generate initial content suggestions for new business accounts"""
        try:
            # Custom logic for new business accounts
            suggestions = {
                "recommendations": [
                    "Create introductory posts about your business",
                    "Share your brand story and mission",
                    "Post product/service highlights"
                ],
                "content_plan": {
                    "first_week": [
                        "Day 1: Brand introduction",
                        "Day 3: Product showcase",
                        "Day 5: Customer testimonial request"
                    ]
                }
            }
            
            return {
                "success": True,
                "message": "Generated initial content suggestions",
                "suggestions": suggestions
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def validate_data_structure(self, data):
        """
        Validate that the data structure contains the required fields.
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Boolean indicating whether the data is valid
        """
        try:
            # Check for required top-level keys
            if not all(key in data for key in ['posts', 'engagement_history']):
                missing_keys = [key for key in ['posts', 'engagement_history'] if key not in data]
                logger.warning(f"Missing required top-level keys in data: {missing_keys}")
                return False
            
            # Check if posts array is populated
            if not data['posts'] or not isinstance(data['posts'], list):
                if not data['posts']:
                    logger.warning("Posts array is empty")
                else:
                    logger.warning(f"Posts is not a list but a {type(data['posts'])}")
                return False
            
            # Check if engagement_history is populated
            if not data['engagement_history'] or not isinstance(data['engagement_history'], list):
                if not data['engagement_history']:
                    logger.warning("Engagement history is empty")
                else:
                    logger.warning(f"Engagement history is not a list but a {type(data['engagement_history'])}")
                return False
            
            # Check at least one post has required fields
            required_post_fields = ['id', 'caption', 'engagement']
            if not any(all(field in post for field in required_post_fields) for post in data['posts']):
                logger.warning("No posts with all required fields")
                # Log what fields are missing from each post
                for i, post in enumerate(data['posts']):
                    missing = [field for field in required_post_fields if field not in post]
                    if missing:
                        logger.warning(f"Post {i} missing fields: {missing}")
                return False
            
            # Check engagement history has required fields
            required_history_fields = ['timestamp', 'engagement']
            if not all(all(field in record for field in required_history_fields) for record in data['engagement_history']):
                logger.warning("Engagement history missing required fields")
                return False
            
            logger.info("Data structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating data structure: {str(e)}")
            return False

    def create_sample_data(self, use_file=False):
        """
        Create sample data when real data isn't available.
        
        Args:
            use_file: Whether to load from a sample file
            
        Returns:
            Dictionary with sample data
        """
        try:
            logger.info("Creating sample data")
            
            if use_file:
                # Try to load from a sample file - implementation depends on your system
                pass
            
            # Create synthetic data
            now = datetime.now()
            # Generate few sample posts
            posts = [
                {
                    'id': '1',
                    'caption': 'Summer fashion trends for 2025 #SummerFashion #Trending',
                    'hashtags': ['#SummerFashion', '#Trending'],
                    'engagement': 1200,
                    'likes': 1000,
                    'comments': 200,
                    'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post1',
                    'type': 'Image'
                },
                {
                    'id': '2',
                    'caption': 'Exciting new product launch! #NewProduct #Promotion',
                    'hashtags': ['#NewProduct', '#Promotion'],
                    'engagement': 800,
                    'likes': 700,
                    'comments': 100,
                    'timestamp': (now - pd.Timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post2',
                    'type': 'Image'
                },
                {
                    'id': '3',
                    'caption': 'Engaging with our community. Thank you for your support! #Community #Engagement',
                    'hashtags': ['#Community', '#Engagement'],
                    'engagement': 1500,
                    'likes': 1300,
                    'comments': 200,
                    'timestamp': (now - pd.Timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post3',
                    'type': 'Image'
                }
            ]
            
            # Create engagement history
            engagement_history = [
                {
                    'timestamp': (now - pd.Timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 1500
                },
                {
                    'timestamp': (now - pd.Timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 800
                },
                {
                    'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 1200
                }
            ]
            
            # Create sample profile
            profile = {
                'username': 'sample_user',
                'fullName': 'Sample User',
                'followersCount': 10000,
                'followsCount': 500,
                'biography': 'This is a sample profile for testing purposes.',
                'account_type': 'unknown'
            }
            
            # Combine into data structure
            data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': profile
            }
            
            logger.info(f"Created sample data with {len(posts)} posts")
            return data
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            # Return minimal data structure
            return {
                'posts': [],
                'engagement_history': [],
                'profile': {}
            }

    def process_instagram_username(self, username, results_limit=10):
        """Updated version that returns object_key"""
        try:
            logger.info(f"Processing Instagram username: {username}")
            
            # Create scraper
            from instagram_scraper import InstagramScraper
            scraper = InstagramScraper()
            
            # Scrape and upload
            scrape_result = scraper.scrape_and_upload(username, results_limit)
            
            if not scrape_result["success"]:
                logger.warning(f"Failed to scrape profile for {username}: {scrape_result['message']}")
                return {"success": False, "message": scrape_result['message']}
            
            # Run pipeline with the uploaded object key
            object_key = scrape_result["object_key"]
            pipeline_result = self.run_pipeline(object_key)
            
            if not pipeline_result["success"]:
                logger.warning(f"Failed to generate recommendations for {username}")
                return {
                    "success": False, 
                    "message": "Failed to generate recommendations",
                    "details": pipeline_result
                }
            
            # Return success with content plan
            return {
                "success": True,
                "message": "Successfully generated recommendations",
                "details": pipeline_result,
                "content_plan_file": "content_plan.json",
                "object_key": object_key  # <-- Return object key
            }
            
        except Exception as e:
            logger.error(f"Error processing Instagram username {username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "message": str(e)}


def main():
    """Main function to run the system."""
    try:
        logger.info("Starting Social Media Content Recommendation System")
        
        # Initialize components
        scraper = InstagramScraper()
        system = ContentRecommendationSystem()
        
        # Check R2 connectivity
        try:
            system.data_retriever.list_objects()
            logger.info("R2 storage is accessible")
        except Exception as e:
            logger.error(f"R2 storage is not accessible: {str(e)}")
            logger.error("Cannot proceed without R2 access")
            return {"success": False, "processed": 0}
        
        # Process pending Instagram usernames
        processed_object_keys = scraper.retrieve_and_process_usernames()
        
        if not processed_object_keys:
            logger.info("No pending usernames to process")
            return {"success": True, "processed": 0}
            
        # Process each scraped dataset
        results = []
        for object_key in processed_object_keys:
            logger.info(f"Processing scraped data: {object_key}")
            result = system.run_pipeline(object_key)
            results.append(result)
            
            # Print results
            print("\n" + "="*50)
            print(f"PROCESSING RESULTS FOR {object_key}")
            print("="*50)
            if result['success']:
                print(f"Success: {result.get('message', 'Operation completed successfully')}")
                print(f"Posts analyzed: {result.get('posts_indexed', 0)}")
                print(f"Recommendations generated: {len(result.get('content_plan', {}).get('improvement_recommendations', []))}")
            else:
                print(f"Failed: {result.get('message', 'Unknown error occurred')}")
        
        return {"success": all(r['success'] for r in results), "processed": len(results)}
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return {"success": False, "processed": 0}


if __name__ == "__main__":
    result = main()
    exit(0 if result["success"] else 1)