"""Configuration settings for the project."""

# R2 Storage Configuration
R2_CONFIG = {
    'endpoint_url': f'https://51abf57b5c6f9b6cf2f91cc87e0b9ffe.r2.cloudflarestorage.com',
    'aws_access_key_id': '2093fa05ee0323bb39de512a19638e78',
    'aws_secret_access_key': 'e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f',
    'bucket_name': 'structuredb',
    'bucket_name2': 'tasks'
}


# Time Series Analysis Configuration
TIME_SERIES_CONFIG = {
    'forecast_periods': 3,  # Number of days to forecast
    'trend_threshold': 0.75  # Threshold for identifying trending content (75th percentile)
}

# Vector Database Configuration
VECTOR_DB_CONFIG = {
    'collection_name': 'social_posts',
    'embedding_model': 'all-MiniLM-L6-v2'  # Sentence transformer model
}

# Gemini API Configuration
GEMINI_CONFIG = {
    'api_key': 'AIzaSyDrvJG2BghzqtSK-HIZ_NsfRWiNwrIk3DQ',
    'model': 'gemini-2.0-flash',
    'max_tokens': 200
}

# Content Templates
CONTENT_TEMPLATES = {
    'promotional': '🚀 New Drop Alert! {caption} {hashtags}',
    'informative': '📢 Did you know? {caption} {hashtags}',
    'engaging': '💬 Let us know what you think! {caption} {hashtags}',
    'trending': '🔥 Trending now: {caption} {hashtags}'
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}