import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB', 'disc_golf_db')
    MYSQL_CURSORCLASS = 'DictCursor'
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = False
    TESTING = False

    # Raise an error if essential variables are not set
    if not SECRET_KEY or not MYSQL_USER or not MYSQL_PASSWORD:
        raise ValueError("Critical environment variables (SECRET_KEY, MYSQL_USER, MYSQL_PASSWORD) are missing.")

class DevelopmentConfig(Config):
    """Configuration for development."""
    DEBUG = True


class TestingConfig(Config):
    """Configuration for testing."""
    TESTING = True
    MYSQL_DB = os.getenv('MYSQL_TEST_DB', 'disc_golf_test_db')  # Separate test database


class ProductionConfig(Config):
    """Configuration for production."""
    DEBUG = False
    TESTING = False