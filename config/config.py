"""
Configuration settings for the OLG Game application.
"""
import os
from dotenv import load_dotenv

class Config:
    """Base configuration class with common settings."""
    
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    DEBUG = False
    TESTING = False
    
    # Application settings
    APP_NAME = 'OLG Classroom Game'
    PORT = int(os.getenv('PORT', 5001))
    
    # Game settings
    DEFAULT_INTEREST_RATE = float(os.getenv('DEFAULT_INTEREST_RATE', '0.03'))
    DEFAULT_BORROWING_LIMIT = float(os.getenv('DEFAULT_BORROWING_LIMIT', '100.0'))
    
    @classmethod
    def get_config(cls):
        """Get configuration dictionary."""
        return {key: value for key, value in cls.__dict__.items()
                if not key.startswith('__') and not callable(value)}


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    ENV = 'development'
    

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    

class ProductionConfig(Config):
    """Production environment configuration."""
    ENV = 'production'
    # In production, ensure SECRET_KEY is properly set in environment
    SECRET_KEY = os.getenv('SECRET_KEY') or 'change-this-in-production'


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get active configuration
def get_config():
    """Get the current active configuration based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, config_by_name['default'])
