from datetime import datetime

# Paths
RAW_DATA_BASE = 'data/raw'
PROCESSED_DATA_BASE = 'data/processed'
LOG_BASE = 'logs/preprocessing'

# Date format
DATE_FORMAT = '%Y-%m-%d'

def get_today():
    return datetime.now().strftime(DATE_FORMAT)

# Input/Output directories
RAW_DATA_DIR = f"{RAW_DATA_BASE}/{get_today()}"
PROCESSED_DATA_DIR = f"{PROCESSED_DATA_BASE}/{get_today()}"
LOG_DIR = f"{LOG_BASE}/{get_today()}"

# Processing settings
SUMMARY_SENTENCE_COUNT = 3  # Số câu trong tóm tắt
MIN_SENTENCE_LENGTH = 10    # Độ dài câu tối thiểu (ký tự)
MAX_SENTENCE_LENGTH = 500   # Độ dài câu tối đa

# TF-IDF settings
USE_IDF = True
SMOOTH_IDF = True
SUBLINEAR_TF = False

# Directory names
ARTICLE_DIR = 'article'
METADATA_DIR = 'metadata'
SUMMARY_DIR = 'summary'
SENTENCES_DIR = 'sentences'  # Optional: để debug
CATEGORY_DIR = 'category'
SUB_CATEGORY_DIR = 'sub-category'