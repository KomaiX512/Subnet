"""Module for generating content recommendations."""

import logging
import re
import json
from .rag_implementation import RagImplementation
from .time_series_analysis import TimeSeriesAnalyzer
from .config import CONTENT_TEMPLATES, LOGGING_CONFIG
from datetime import datetime
import pandas as pd

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class RecommendationGenerator:
    """Class for generating content recommendations."""
    
    def __init__(self, rag=None, time_series=None, templates=CONTENT_TEMPLATES):
        """Initialize with necessary components."""
        self.rag = rag or RagImplementation()
        self.time_series = time_series or TimeSeriesAnalyzer()
        self.templates = templates
    
    def extract_hashtags(self, text):
        """
        Extract hashtags from text.
        
        Args:
            text: Text containing hashtags
            
        Returns:
            List of hashtags
        """
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def format_caption(self, raw_text):
        """
        Format caption by removing hashtags.
        
        Args:
            raw_text: Raw text with hashtags
            
        Returns:
            Dictionary with formatted caption and hashtags
        """
        hashtags = self.extract_hashtags(raw_text)
        caption = re.sub(r'#\w+', '', raw_text).strip()
        
        return {
            "caption": caption,
            "hashtags": hashtags
        }
    
    def apply_template(self, recommendation, template_key="promotional"):
        """
        Apply a template to the recommendation.
        
        Args:
            recommendation: Dictionary with recommendation details
            template_key: Key of template to apply
            
        Returns:
            Formatted string
        """
        try:
            template = self.templates.get(template_key, self.templates["promotional"])
            
            caption = recommendation.get("caption", "")
            hashtags = recommendation.get("hashtags", [])
            hashtags_str = " ".join(hashtags)
            
            formatted = template.format(caption=caption, hashtags=hashtags_str)
            return formatted
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return f"{recommendation.get('caption', '')} {' '.join(recommendation.get('hashtags', []))}"
    
    def generate_trending_topics(self, data, timestamp_col='timestamp', value_col='engagement', top_n=3):
        """
        Generate trending topics based on time series analysis.
        
        Args:
            data: Dictionary or DataFrame with time series data
            timestamp_col: Column name for timestamps
            value_col: Column name for values
            top_n: Number of trending topics to return
            
        Returns:
            List of trending topics with periods
        """
        try:
            # Analyze data
            results = self.time_series.analyze_data(data, timestamp_col, value_col)
            
            # Get trending periods
            trending_periods = list(results.get('trending_periods', pd.DataFrame()).iterrows())[:top_n]
            
            if trending_periods is None or len(trending_periods) == 0:
                logger.warning("No trending periods detected")
                return []
            
            # Format trending periods
            trending_topics = []
            for _, row in trending_periods:
                trending_topics.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'value': row['yhat'],
                    'topic': f"Trending on {row['ds'].strftime('%B %d')}"
                })
            
            logger.info(f"Generated {len(trending_topics)} trending topics")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error generating trending topics: {str(e)}")
            return []
    
    def generate_recommendations(self, topics, n_per_topic=3):
        """
        Generate content recommendations for multiple topics.
        
        Args:
            topics: List of topics to generate recommendations for
            n_per_topic: Number of recommendations per topic
            
        Returns:
            Dictionary with recommendations by topic
        """
        try:
            if not topics or n_per_topic <= 0:
                logger.warning("Invalid input for generate_recommendations")
                return {}

            # Validate topic types
            if not all(isinstance(topic, (str, dict)) for topic in topics):
                logger.error("Invalid topic format - must be strings or dictionaries")
                return {}

            # Convert dictionary topics to strings if needed
            topic_strings = []
            for topic in topics:
                if isinstance(topic, dict):
                    topic_str = topic.get('topic', '').strip() or str(topic)
                    topic_strings.append(topic_str)
                else:
                    topic_strings.append(str(topic).strip())

            # Remove empty topics
            valid_topics = [t for t in topic_strings if t]
            if not valid_topics:
                logger.error("No valid topics provided for recommendations")
                return {}

            # Batch all topics into a single RAG request
            combined_prompt = self._create_batch_prompt(valid_topics)
            
            # Generate a single response for all topics
            batch_response = self.rag.generate_batch_recommendations(combined_prompt, valid_topics)
            
            # Process the batch response into individual recommendations
            recommendations = {}
            
            for topic in valid_topics:
                if topic in batch_response:
                    topic_recs = batch_response[topic]
                    # Ensure we have the requested number of recommendations
                    while len(topic_recs) < n_per_topic:
                        # Generate additional recommendations if needed
                        additional_rec = self.rag.generate_recommendation(topic)
                        topic_recs.append(additional_rec)
                    
                    # Store recommendations for this topic
                    recommendations[topic] = topic_recs[:n_per_topic]
                else:
                    # Generate recommendations individually if not in batch response
                    logger.warning(f"Topic {topic} not found in batch response, generating individually")
                    topic_recs = []
                    for i in range(n_per_topic):
                        rec = self.rag.generate_recommendation(topic)
                        topic_recs.append(rec)
                    recommendations[topic] = topic_recs
            
            logger.info(f"Generated recommendations for {len(valid_topics)} topics")
            return recommendations
        except Exception as e:
            logger.error(f"Critical error in generate_recommendations: {str(e)}")
            return {}
    
    def _create_batch_prompt(self, topics):
        """Create a prompt for batch recommendation generation."""
        topics_str = ", ".join([f'"{topic}"' for topic in topics])
        
        prompt = f"""
        You are an expert social media content creator. I need you to generate content recommendations 
        for the following topics: {topics_str}.
        
        For each topic, provide 3 different content ideas. Each idea should include:
        1. An attention-grabbing caption
        2. Relevant hashtags
        3. A call to action
        
        Format your response as a JSON object with topics as keys and arrays of recommendations as values:
        
        {{
            "topic1": [
                {{
                    "caption": "Caption for first recommendation",
                    "hashtags": ["#Hashtag1", "#Hashtag2"],
                    "call_to_action": "Call to action text"
                }},
                // More recommendations...
            ],
            "topic2": [
                // Recommendations for topic 2...
            ]
        }}
        
        Be creative and engaging. Use the specific topic keywords in your recommendations.
        """
        
        return prompt
    
    def analyze_account_type(self, posts):
        """
        Analyze posts to determine if the account is for branding or personal use.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with account type analysis
        """
        try:
            # Extract captions and hashtags
            captions = [post.get('caption', '') for post in posts if 'caption' in post]
            all_hashtags = []
            for post in posts:
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
            
            # Count business-related terms in captions
            business_terms = ['product', 'sale', 'discount', 'offer', 'brand', 'business', 
                             'shop', 'store', 'buy', 'purchase', 'collection', 'launch']
            
            business_count = sum(1 for caption in captions 
                               if any(term in caption.lower() for term in business_terms))
            
            # Count business-related hashtags
            business_hashtags = ['#business', '#brand', '#product', '#sale', '#shop', 
                                '#store', '#entrepreneur', '#marketing']
            
            business_hashtag_count = sum(1 for hashtag in all_hashtags 
                                      if any(bh.lower() in hashtag.lower() for bh in business_hashtags))
            
            # Calculate percentages
            total_posts = len(posts)
            if total_posts == 0:
                return {
                    'account_type': 'Unknown',
                    'confidence': 0,
                    'analysis': 'Insufficient data to determine account type'
                }
            
            business_caption_percentage = (business_count / total_posts) * 100
            
            # Determine account type
            if business_caption_percentage > 60 or business_hashtag_count > total_posts * 0.5:
                account_type = 'Business/Brand'
                confidence = min(100, max(60, business_caption_percentage))
                analysis = f"Account appears to be for business/branding purposes with {confidence:.1f}% confidence. Found {business_count} posts with business-related terms and {business_hashtag_count} business-related hashtags."
            else:
                account_type = 'Personal'
                confidence = min(100, max(60, 100 - business_caption_percentage))
                analysis = f"Account appears to be for personal use with {confidence:.1f}% confidence. Only {business_count} out of {total_posts} posts contain business-related terms."
            
            return {
                'account_type': account_type,
                'confidence': confidence,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing account type: {str(e)}")
            return {
                'account_type': 'Unknown',
                'confidence': 0,
                'analysis': f"Error during analysis: {str(e)}"
            }
    
    def analyze_engagement(self, posts):
        """
        Analyze which types of posts have the most engagement.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with engagement analysis
        """
        try:
            # Group posts by content type
            content_types = {
                'photo': [],
                'video': [],
                'carousel': [],
                'text_only': []
            }
            
            # Categorize posts by hashtags
            hashtag_categories = {
                'product': ['#product', '#sale', '#shop', '#store', '#buy'],
                'lifestyle': ['#lifestyle', '#life', '#daily', '#everyday'],
                'motivation': ['#motivation', '#inspire', '#success', '#goals'],
                'fashion': ['#fashion', '#style', '#outfit', '#clothing'],
                'food': ['#food', '#recipe', '#cooking', '#foodie'],
                'travel': ['#travel', '#vacation', '#trip', '#adventure'],
                'fitness': ['#fitness', '#workout', '#gym', '#health']
            }
            
            category_engagement = {category: {'count': 0, 'total_engagement': 0} 
                                for category in hashtag_categories.keys()}
            
            # Process each post
            for post in posts:
                # Get post type
                post_type = post.get('media_type', 'photo').lower()
                if post_type in content_types:
                    content_types[post_type].append(post)
                else:
                    content_types['photo'].append(post)
                
                # Get engagement
                engagement = post.get('engagement', 0)
                if not engagement and 'likes' in post:
                    # Calculate engagement from likes and comments if available
                    likes = post.get('likes', 0)
                    comments = post.get('comments', 0)
                    engagement = likes + comments
                
                # Categorize by hashtags
                post_hashtags = []
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        post_hashtags = post['hashtags']
                    elif isinstance(post['hashtags'], str):
                        post_hashtags = self.extract_hashtags(post['hashtags'])
                
                # Check which categories the hashtags belong to
                for category, category_tags in hashtag_categories.items():
                    if any(ht.lower() in [t.lower() for t in post_hashtags] for ht in category_tags):
                        category_engagement[category]['count'] += 1
                        category_engagement[category]['total_engagement'] += engagement
            
            # Calculate average engagement by content type
            content_type_analysis = {}
            for content_type, type_posts in content_types.items():
                if type_posts:
                    total_engagement = sum(post.get('engagement', 0) for post in type_posts)
                    avg_engagement = total_engagement / len(type_posts) if len(type_posts) > 0 else 0
                    content_type_analysis[content_type] = {
                        'count': len(type_posts),
                        'total_engagement': total_engagement,
                        'average_engagement': avg_engagement
                    }
            
            # Calculate average engagement by category
            category_analysis = {}
            for category, data in category_engagement.items():
                if data['count'] > 0:
                    avg_engagement = data['total_engagement'] / data['count']
                    category_analysis[category] = {
                        'count': data['count'],
                        'total_engagement': data['total_engagement'],
                        'average_engagement': avg_engagement
                    }
            
            # Find best performing content type and category
            best_content_type = max(content_type_analysis.items(), 
                                  key=lambda x: x[1]['average_engagement'], 
                                  default=(None, {'average_engagement': 0}))
            
            best_category = max(category_analysis.items(), 
                              key=lambda x: x[1]['average_engagement'], 
                              default=(None, {'average_engagement': 0}))
            
            # Generate summary
            if best_content_type[0] and best_category[0]:
                summary = f"The account performs best with {best_content_type[0]} content about {best_category[0]}. " \
                         f"Average engagement for {best_content_type[0]} content is {best_content_type[1]['average_engagement']:.1f}, " \
                         f"and for {best_category[0]} content is {best_category[1]['average_engagement']:.1f}."
            else:
                summary = "Insufficient data to determine best performing content."
            
            return {
                'content_type_analysis': content_type_analysis,
                'category_analysis': category_analysis,
                'best_performing_content': best_content_type[0],
                'best_performing_category': best_category[0],
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return {
                'summary': f"Error during engagement analysis: {str(e)}"
            }
    
    def analyze_posting_trends(self, posts):
        """
        Analyze posting patterns related to product trends and events.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with posting trend analysis
        """
        try:
            # Extract timestamps and convert to datetime
            timestamps = []
            for post in posts:
                if 'timestamp' in post:
                    try:
                        timestamps.append(pd.to_datetime(post['timestamp']))
                    except:
                        continue
            
            if not timestamps:
                return {
                    'summary': "Insufficient timestamp data to analyze posting trends."
                }
            
            # Create DataFrame with timestamps
            df = pd.DataFrame({'timestamp': timestamps})
            
            # Extract day of week and hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['hour'] = df['timestamp'].dt.hour
            
            # Count posts by day of week
            day_counts = df['day_of_week'].value_counts().to_dict()
            
            # Count posts by hour
            hour_counts = df['hour'].value_counts().to_dict()
            
            # Find most common posting days and times
            most_common_day = max(day_counts.items(), key=lambda x: x[1], default=(None, 0))
            most_common_hour = max(hour_counts.items(), key=lambda x: x[1], default=(None, 0))
            
            # Format hour in 12-hour format
            hour_formatted = f"{most_common_hour[0] % 12 or 12} {'AM' if most_common_hour[0] < 12 else 'PM'}"
            
            # Calculate posting frequency
            date_range = max(timestamps) - min(timestamps)
            days_range = date_range.days + 1  # Add 1 to include both start and end dates
            posts_per_day = len(timestamps) / days_range if days_range > 0 else 0
            
            # Check for seasonal patterns
            df['month'] = df['timestamp'].dt.month
            month_counts = df['month'].value_counts().to_dict()
            
            # Identify months with higher posting frequency
            avg_posts_per_month = len(timestamps) / 12  # Simple average
            high_activity_months = {month: count for month, count in month_counts.items() 
                                  if count > avg_posts_per_month * 1.2}  # 20% above average
            
            month_names = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            
            high_activity_months_named = {month_names[month]: count 
                                        for month, count in high_activity_months.items()}
            
            # Generate summary
            if most_common_day[0] and most_common_hour[0] is not None:
                posting_pattern = f"Posts most frequently on {most_common_day[0]}s at around {hour_formatted}."
            else:
                posting_pattern = "No clear posting pattern detected."
            
            if high_activity_months_named:
                seasonal_pattern = f"Higher posting activity during: {', '.join(high_activity_months_named.keys())}."
            else:
                seasonal_pattern = "No clear seasonal posting pattern detected."
            
            summary = f"{posting_pattern} Average posting frequency is {posts_per_day:.1f} posts per day. {seasonal_pattern}"
            
            return {
                'most_active_day': most_common_day[0],
                'most_active_hour': most_common_hour[0],
                'hour_formatted': hour_formatted,
                'posts_per_day': posts_per_day,
                'day_distribution': day_counts,
                'hour_distribution': hour_counts,
                'high_activity_months': high_activity_months_named,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing posting trends: {str(e)}")
            return {
                'summary': f"Error during posting trend analysis: {str(e)}"
            }
    
    def generate_next_post_prediction(self, posts, account_analysis=None):
        """
        Generate predictions for the next post.
        
        Args:
            posts: List of post dictionaries
            account_analysis: Optional dictionary with account analysis results
            
        Returns:
            Dictionary with next post prediction
        """
        try:
            # Extract recent captions and hashtags for context
            recent_captions = [post.get('caption', '') for post in posts[-5:] if 'caption' in post]
            
            all_hashtags = []
            for post in posts:
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
            
            # Count hashtag frequency
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            common_hashtags = [tag for tag, count in hashtag_counts.most_common(10)]
            
            # Use RAG to generate prediction
            context = "\n".join([
                f"Recent caption: {caption}" for caption in recent_captions
            ])
            
            context += "\nCommonly used hashtags: " + ", ".join(common_hashtags)
            
            if account_analysis:
                if 'account_type' in account_analysis:
                    context += f"\nAccount type: {account_analysis['account_type']}"
                
                if 'engagement' in account_analysis and 'best_performing_category' in account_analysis['engagement']:
                    context += f"\nBest performing content category: {account_analysis['engagement']['best_performing_category']}"
                
                if 'posting_trends' in account_analysis and 'summary' in account_analysis['posting_trends']:
                    context += f"\nPosting trends: {account_analysis['posting_trends']['summary']}"
            
            # Generate prediction using RAG
            prompt = f"""
            Based on the following context about an Instagram account:
            
            {context}
            
            Generate a prediction for their next post, including:
            1. A caption that matches their style
            2. Relevant hashtags they would likely use
            3. A call to action consistent with their previous posts
            4. A brief image prompt that could be used with an AI image generator to create a suitable image
            
            Format your response as a JSON object with the following structure:
            {{
                "caption": "Predicted caption text",
                "hashtags": ["#hashtag1", "#hashtag2", ...],
                "call_to_action": "Predicted call to action",
                "image_prompt": "Detailed image prompt for AI generator"
            }}
            """
            
            # Use RAG to generate the prediction
            prediction = self.rag.generate_recommendation(prompt)
            
            # Ensure all required fields are present
            if 'image_prompt' not in prediction:
                prediction['image_prompt'] = "A high-quality, professional image that matches the caption and hashtags."
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating next post prediction: {str(e)}")
            return {
                'caption': "Error generating prediction",
                'hashtags': ["#error"],
                'call_to_action': "Please try again later",
                'image_prompt': "Error generating image prompt"
            }
    
    def identify_competitors(self, posts, profile_info=None):
        """
        Identify potential competitors based on content and hashtags.
        
        Args:
            posts: List of post dictionaries
            profile_info: Optional dictionary with profile information
            
        Returns:
            List of potential competitors with analysis
        """
        try:
            # Extract all hashtags and mentions
            all_hashtags = []
            all_mentions = []
            
            for post in posts:
                # Extract hashtags
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
                
                # Extract mentions from captions
                if 'caption' in post:
                    mentions = re.findall(r'@(\w+)', post['caption'])
                    all_mentions.extend(mentions)
            
            # Count frequency
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            mention_counts = Counter(all_mentions)
            
            # Get top hashtags and mentions
            top_hashtags = [tag for tag, _ in hashtag_counts.most_common(20)]
            top_mentions = [mention for mention, _ in mention_counts.most_common(20)]
            
            # Create context for RAG
            context = ""
            if profile_info and 'bio' in profile_info:
                context += f"Account bio: {profile_info['bio']}\n"
            
            if profile_info and 'category' in profile_info:
                context += f"Account category: {profile_info['category']}\n"
            
            context += f"Top hashtags used: {', '.join(top_hashtags[:10])}\n"
            context += f"Accounts frequently mentioned: {', '.join(top_mentions[:5])}\n"
            
            # Use RAG to identify competitors
            prompt = f"""
            Based on the following information about an Instagram account:
            
            {context}
            
            Identify 10 potential competitors or similar accounts that would appeal to the same audience.
            For each competitor, provide:
            1. A suggested account name
            2. Why they are a competitor
            3. What makes them different or unique
            
            Format your response as a JSON array with the following structure:
            [
                {{
                    "account_name": "competitor1",
                    "reason": "Why they are a competitor",
                    "unique_value": "What makes them different"
                }},
                ...
            ]
            
            Be specific and realistic in your suggestions. If the account appears to be in a specific niche or industry,
            suggest real competitors in that space.
            """
            
            # Use RAG to generate competitors
            response = self.rag.generate_recommendation(prompt)
            
            # Extract competitors from response
            competitors = []
            if isinstance(response, dict) and 'competitors' in response:
                competitors = response['competitors']
            elif isinstance(response, list):
                competitors = response
            else:
                # Create a basic list if the response format is unexpected
                competitors = [
                    {
                        "account_name": f"competitor_{i+1}",
                        "reason": "Similar content and audience",
                        "unique_value": "Different approach to similar topics"
                    }
                    for i in range(10)
                ]
            
            # Ensure we have at least 10 competitors
            while len(competitors) < 10:
                competitors.append({
                    "account_name": f"suggested_account_{len(competitors)+1}",
                    "reason": "Similar content and target audience",
                    "unique_value": "Different perspective on similar topics"
                })
            
            return competitors[:10]  # Return exactly 10 competitors
            
        except Exception as e:
            logger.error(f"Error identifying competitors: {str(e)}")
            # Return a basic list of 10 competitors
            return [
                {
                    "account_name": f"competitor_{i+1}",
                    "reason": "Similar content and audience",
                    "unique_value": "Different approach to similar topics"
                }
                for i in range(10)
            ]
    
    def generate_improvement_recommendations(self, account_analysis):
        """
        Generate personalized improvement recommendations based on account analysis.
        
        Args:
            account_analysis: Dictionary with account analysis results
            
        Returns:
            Dictionary with improvement recommendations
        """
        try:
            # Ensure account_analysis is properly formatted
            if not isinstance(account_analysis, dict):
                logger.warning("Invalid account analysis format - using fallback")
                return [{"recommendation": "Post more consistently"}]

            # Safely extract account type with fallbacks
            account_type = account_analysis.get('account_type', 'Unknown')
            if not isinstance(account_type, str):  # Handle unexpected types
                account_type = str(account_type)

            # Extract relevant information from account analysis
            context = ""
            
            if 'account_type' in account_analysis:
                context += f"Account type: {account_analysis['account_type']['account_type']}\n"
                context += f"Account analysis: {account_analysis['account_type']['analysis']}\n"
            
            if 'engagement' in account_analysis:
                context += f"Engagement analysis: {account_analysis['engagement']['summary']}\n"
            
            if 'posting_trends' in account_analysis:
                context += f"Posting trends: {account_analysis['posting_trends']['summary']}\n"
            
            # Use RAG to generate recommendations
            prompt = f"""
            Based on the following analysis of an Instagram account:
            
            {context}
            
            Generate 5 specific, actionable recommendations for how the account holder can improve their Instagram presence.
            For each recommendation, provide:
            1. A clear, specific action item
            2. Why this would help (the reasoning)
            3. How to implement it (practical steps)
            
            Format your response as a JSON array with the following structure:
            [
                {{
                    "recommendation": "Clear action item",
                    "reasoning": "Why this would help",
                    "implementation": "How to implement it"
                }},
                ...
            ]
            
            Be specific, practical, and tailored to the account's current performance.
            """
            
            # Use RAG to generate recommendations
            response = self.rag.generate_recommendation(prompt)
            
            # Extract recommendations from response
            recommendations = []
            if isinstance(response, dict) and 'recommendations' in response:
                recommendations = response['recommendations']
            elif isinstance(response, list):
                recommendations = response
            else:
                # Create basic recommendations if the response format is unexpected
                recommendations = [
                    {
                        "recommendation": "Post more consistently",
                        "reasoning": "Regular posting helps maintain audience engagement",
                        "implementation": "Create a content calendar and schedule posts in advance"
                    },
                    {
                        "recommendation": "Engage more with followers",
                        "reasoning": "Higher engagement leads to better reach and loyalty",
                        "implementation": "Respond to comments and messages promptly"
                    },
                    {
                        "recommendation": "Use more relevant hashtags",
                        "reasoning": "Proper hashtags increase discoverability",
                        "implementation": "Research trending hashtags in your niche"
                    },
                    {
                        "recommendation": "Improve visual consistency",
                        "reasoning": "Consistent aesthetics create a recognizable brand",
                        "implementation": "Use similar filters and color schemes across posts"
                    },
                    {
                        "recommendation": "Collaborate with similar accounts",
                        "reasoning": "Collaborations expose your account to new audiences",
                        "implementation": "Reach out to complementary accounts for partnership opportunities"
                    }
                ]
            
            # Ensure we have at least 5 recommendations
            while len(recommendations) < 5:
                recommendations.append({
                    "recommendation": f"Generic recommendation {len(recommendations)+1}",
                    "reasoning": "This will help improve your account performance",
                    "implementation": "Follow best practices for Instagram growth"
                })
            
            return recommendations[:5]  # Return exactly 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {str(e)}")
            # Return basic recommendations
            return [
                {
                    "recommendation": "Post more consistently",
                    "reasoning": "Regular posting helps maintain audience engagement",
                    "implementation": "Create a content calendar and schedule posts in advance"
                },
                {
                    "recommendation": "Engage more with followers",
                    "reasoning": "Higher engagement leads to better reach and loyalty",
                    "implementation": "Respond to comments and messages promptly"
                },
                {
                    "recommendation": "Use more relevant hashtags",
                    "reasoning": "Proper hashtags increase discoverability",
                    "implementation": "Research trending hashtags in your niche"
                },
                {
                    "recommendation": "Improve visual consistency",
                    "reasoning": "Consistent aesthetics create a recognizable brand",
                    "implementation": "Use similar filters and color schemes across posts"
                },
                {
                    "recommendation": "Collaborate with similar accounts",
                    "reasoning": "Collaborations expose your account to new audiences",
                    "implementation": "Reach out to complementary accounts for partnership opportunities"
                }
            ]
    
    def generate_content_plan(self, data):
        """Generate complete content plan with all recommendations."""
        try:
            if not data or not data.get('posts'):
                logger.error("Cannot generate content plan - no posts in data")
                return None
                
            posts = data['posts']
            engagement_data = data.get('engagement_history', [])
            
            # 1. Perform account analysis
            account_analysis = self.analyze_account_type(posts)
            if not account_analysis:
                logger.warning("Failed to generate account analysis")
                account_analysis = {'account_type': 'Unknown'}  # Add default
            
            # 2. Analyze engagement patterns
            engagement_analysis = self.analyze_engagement(posts)
            if not engagement_analysis:
                logger.warning("Failed to generate engagement analysis")
                engagement_analysis = {'summary': 'No engagement analysis available'}  # Add default
            
            # 3. Analyze posting trends
            posting_trends = self.analyze_posting_trends(posts)
            if not posting_trends:
                logger.warning("Failed to analyze posting trends")
                posting_trends = {'summary': 'No posting trend analysis available'}  # Add default
            
            # 4. Generate next post prediction (CRUCIAL FIX)
            next_post = self.generate_next_post_prediction(posts, account_analysis)
            if not next_post:  # Add fallback if prediction fails
                logger.warning("Using fallback next post prediction")
                next_post = {
                    "caption": "Check out our latest updates!",
                    "hashtags": ["#New", "#Update"],
                    "call_to_action": "Visit our profile for more",
                    "image_prompt": "Modern lifestyle image with vibrant colors"
                }
            
            # 5. Generate improvement recommendations
            improvement_recs = self.generate_improvement_recommendations(account_analysis)
            if not improvement_recs:  # Add fallback
                improvement_recs = [{"recommendation": "Post more consistently"}]
            
            # 6. Identify competitors
            competitors = self.identify_competitors(posts, data.get('profile'))
            if not competitors:  # Add default
                competitors = {"similar_accounts": []}
            
            # Compile final content plan
            content_plan = {
                'generated_date': datetime.now().isoformat(),
                'profile_analysis': account_analysis,
                'engagement_analysis': engagement_analysis,
                'posting_trends': posting_trends,
                'next_post_prediction': next_post,  # WAS MISSING
                'improvement_recommendations': improvement_recs,
                'competitors': competitors
            }
            
            # Add trending topics if available
            if engagement_data:
                trending = self.generate_trending_topics(engagement_data)
                if trending:
                    content_plan['trending_topics'] = trending
            
            logger.info(f"Generated content plan with {len(improvement_recs)} recommendations")
            return content_plan
            
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            return None


# Test function
def test_recommendation_generation():
    """Test the recommendation generation functionality."""
    try:
        # Create generator
        generator = RecommendationGenerator()
        
        # Test hashtag extraction
        text = "Check out our summer sale! #SummerSale #Discount"
        hashtags = generator.extract_hashtags(text)
        if len(hashtags) != 2:
            logger.warning(f"Expected 2 hashtags, got {len(hashtags)}")
        
        # Test caption formatting
        formatted = generator.format_caption(text)
        if formatted["caption"] != "Check out our summer sale!":
            logger.warning(f"Caption formatting issue: {formatted['caption']}")
        
        # Test template application
        recommendation = {
            "caption": "New summer collection available now!",
            "hashtags": ["#Summer", "#NewCollection"]
        }
        formatted = generator.apply_template(recommendation, "promotional")
        if "New summer collection available now!" not in formatted:
            logger.warning(f"Template application issue: {formatted}")
        
        # Test recommendation generation
        topics = ["summer fashion", "fall trends"]
        recommendations = generator.generate_recommendations(topics)
        
        if len(recommendations) == len(topics):
            logger.info("Recommendation generation test successful")
            return True
        else:
            logger.warning("Recommendation count mismatch")
            return False
            
    except Exception as e:
        logger.error(f"Recommendation generation test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test recommendation generation
    success = test_recommendation_generation()
    print(f"Recommendation generation test {'successful' if success else 'failed'}")