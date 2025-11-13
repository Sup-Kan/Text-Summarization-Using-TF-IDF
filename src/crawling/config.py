"""
Cấu hình cho news crawler
"""

from datetime import datetime

# URL và headers
URL = "https://baochinhphu.vn"

HEADERS = {
    'User-Agent': 'YOUR_USER_AGENT',
    'Accept': 'YOUR_ACCEPT_HEADERS',
    'Accept-Language': 'YOUR_LANGUAGE',
    'Connection': 'keep-alive',
}

# Timing
DELAY_BETWEEN_REQUESTS = 1
DELAY_BETWEEN_SUBCATEGORIES = 2
DELAY_BETWEEN_CATEGORIES = 3
REQUEST_TIMEOUT = 15

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5

# Paths
BASE_DATA_DIR = 'data/raw'
LOG_BASE_DIR = 'logs/crawling'

# Date format cho thư mục
DATE_FORMAT = '%Y-%m-%d'  # Format: YYYY-MM-DD

# Tự động tạo thư mục theo ngày hôm nay
def get_today_dir():
    """Lấy thư mục cho ngày hôm nay."""
    today = datetime.now().strftime(DATE_FORMAT)
    return today

# Output directory sẽ là: data/raw/YYYY-MM-DD/
OUTPUT_DIR = f"{BASE_DATA_DIR}/{get_today_dir()}"
LOG_DIR = f"{LOG_BASE_DIR}/{get_today_dir()}"

# Excluded categories
EXCLUDED_CATEGORIES = ['trang chủ', 'góp ý hiến kế']

# Limits
DEFAULT_MAX_CATEGORIES = None
DEFAULT_MAX_SUBCATEGORIES = None
DEFAULT_MAX_ARTICLES = 5

# Directory structure
ARTICLE_DIR = 'article'
METADATA_DIR = 'metadata'
CATEGORY_DIR = 'category'
SUB_CATEGORY_DIR = 'sub-category'