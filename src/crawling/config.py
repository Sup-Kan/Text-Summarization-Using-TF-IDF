# src/crawling/config.py

"""Crawling configuration"""

from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
# URLs
URL = "https://baochinhphu.vn"

HEADERS = {
    'User-Agent': os.getenv('CRAWL_USER_AGENT', 'Mozilla/5.0'),
    'Accept': os.getenv('CRAWL_ACCEPT'),
    'Accept-Language': os.getenv('CRAWL_ACCEPT_LANGUAGE'),
    'Connection': 'keep-alive'
}

# Timing
DELAY_BETWEEN_REQUESTS = 1
DELAY_BETWEEN_SUBCATEGORIES = 2
DELAY_BETWEEN_CATEGORIES = 3
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 5

# Paths
BASE_DATA_DIR = os.getenv('DATA_RAW_DIR', 'data/raw')
LOG_BASE_DIR = os.getenv('LOGS_DIR', 'logs') + '/crawling'
DATE_FORMAT = '%Y-%m-%d'

def get_today():
    return datetime.now().strftime(DATE_FORMAT)

OUTPUT_DIR = f"{BASE_DATA_DIR}/{get_today()}"
LOG_DIR = f"{LOG_BASE_DIR}/{get_today()}"

# Limits
DEFAULT_MAX_CATEGORIES = int(os.getenv('CRAWL_MAX_CATEGORIES', 10))
DEFAULT_MAX_SUBCATEGORIES = 5
DEFAULT_MAX_ARTICLES = int(os.getenv('CRAWL_MAX_ARTICLES', 20))

# Directory structure
ARTICLE_DIR = 'article'
METADATA_DIR = 'metadata'
CATEGORY_DIR = 'category'
SUB_CATEGORY_DIR = 'sub-category'

# Excluded
EXCLUDED_CATEGORIES = ['trang chủ', 'góp ý hiến kế']