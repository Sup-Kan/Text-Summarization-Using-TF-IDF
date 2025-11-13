from datetime import datetime
from pathlib import Path
import os

# ==================== PATHS ====================
RAW_DATA_BASE = 'data/raw'
PROCESSED_DATA_BASE = 'data/processed'
LOG_BASE = 'logs/preprocessing'

# VnCoreNLP resources
VNCORENLP_DIR = 'models/vncorenlp'
VNCORENLP_JAR = 'VnCoreNLP-1.2.jar'
VNCORENLP_DOWNLOAD_URL = 'https://github.com/vncorenlp/VnCoreNLP/archive/refs/tags/v1.2.zip'

# Stopwords path
STOPWORDS_FILE = os.path.join(VNCORENLP_DIR, 'stopwords', 'vietnamese-stopwords.txt')

# Date format
DATE_FORMAT = '%Y-%m-%d'

def get_today():
    return datetime.now().strftime(DATE_FORMAT)

# Input/Output directories
RAW_DATA_DIR = f"{RAW_DATA_BASE}/{get_today()}"
PROCESSED_DATA_DIR = f"{PROCESSED_DATA_BASE}/{get_today()}"
LOG_DIR = f"{LOG_BASE}/{get_today()}"

# ==================== PROCESSING SETTINGS ====================
SUMMARY_SENTENCE_COUNT = 3  # Số câu trong tóm tắt
MIN_SENTENCE_LENGTH = 10    # Độ dài câu tối thiểu (ký tự)
MAX_SENTENCE_LENGTH = 500   # Độ dài câu tối đa

# ==================== TF-IDF SETTINGS ====================
USE_IDF = True
SMOOTH_IDF = True
SUBLINEAR_TF = False

# ==================== VNCORENLP SETTINGS ====================
VNCORENLP_HOST = "http://127.0.0.1"
VNCORENLP_PORT = 9000
VNCORENLP_ANNOTATORS = "wseg"  # Word segmentation
VNCORENLP_MAX_HEAP_SIZE = "-Xmx2g"  # Java heap size

# ==================== DIRECTORY NAMES ====================
ARTICLE_DIR = 'article'
METADATA_DIR = 'metadata'
SUMMARY_DIR = 'summary'
SENTENCES_DIR = 'sentences'
CATEGORY_DIR = 'category'
SUB_CATEGORY_DIR = 'sub-category'