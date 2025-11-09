"""
Utility functions
"""

import re
import logging
import sys
from pathlib import Path
from functools import wraps
import time
from datetime import datetime

# Global logger instance
_logger = None

def setup_logging(log_dir):
    """
    Setup logging configuration - PHẢI GỌI ĐẦU TIÊN.
    """
    global _logger
    
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / 'crawler.log'
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create module logger
    _logger = logging.getLogger('news_crawler')
    _logger.setLevel(logging.DEBUG)
    
    # Test logging
    _logger.info("=" * 80)
    _logger.info("Logging system initialized")
    _logger.info(f"Log file: {log_file.absolute()}")
    _logger.info("=" * 80)
    
    # Verify file was created
    if log_file.exists():
        print(f"✓ Log file created: {log_file.absolute()}")
    else:
        print(f"✗ WARNING: Log file not created at {log_file.absolute()}")
    
    return _logger

def get_logger(name=None):
    """Get logger instance."""
    if name:
        return logging.getLogger(name)
    return logging.getLogger('news_crawler')

def create_latest_symlink(base_dir, today_dir):
    """
    Tạo symlink 'latest' trỏ đến thư mục mới nhất.
    
    Args:
        base_dir: Thư mục gốc (ví dụ: /content/data/raw)
        today_dir: Tên thư mục ngày hôm nay (ví dụ: 2025-11-09)
    """
    logger = get_logger()
    
    try:
        base_path = Path(base_dir)
        today_path = base_path / today_dir
        latest_link = base_path / 'latest'
        
        # Xóa symlink cũ nếu có
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
            logger.debug(f"Removed old 'latest' symlink")
        
        # Tạo symlink mới (relative path)
        latest_link.symlink_to(today_dir)
        logger.info(f"Created 'latest' symlink -> {today_dir}")
        print(f"✓ Created symlink: {latest_link} -> {today_dir}")
        
    except Exception as e:
        logger.warning(f"Could not create symlink: {e}")
        print(f"⚠ Warning: Could not create 'latest' symlink: {e}")

def get_crawl_date():
    """Lấy ngày crawl hiện tại (format: YYYY-MM-DD)."""
    return datetime.now().strftime('%Y-%m-%d')

def get_crawl_datetime():
    """Lấy datetime crawl hiện tại (format: YYYY-MM-DD HH:MM:SS)."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def retry(max_attempts=3, delay=5, exceptions=(Exception,)):
    """Decorator để retry function khi gặp lỗi."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt}/{max_attempts} failed: {str(e)}. Retrying in {delay}s...")
                    time.sleep(delay)
            
        return wrapper
    return decorator

def sanitize_filename(name):
    """Sanitize string for use as filename."""
    sanitized = re.sub(r'[\x00-\x1F\\/:*?"<>|]', '_', name).strip()
    sanitized = re.sub(r'_{2,}', '_', sanitized)
    return sanitized[:100]

def create_directory(base_dir):
    """Create directory if it doesn't exist."""
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def normalize_url(link, base_url):
    """Normalize URL."""
    if not link:
        return None
    if link.startswith('http://') or link.startswith('https://'):
        return link
    link = re.sub(r'^\.+/', '', link)
    
    if link.startswith('/'):
        return base_url + link
    return base_url + '/' + link

def print_separator():
    """Print separator line."""
    print("-" * 80)

def print_progress(message, level=0):
    """Print progress message with indentation."""
    indent = "  " * level
    print(f"{indent}{message}")
    
    # Also log to file
    logger = get_logger()
    logger.debug(f"{'  ' * level}{message}")

def extract_date_from_text(text):
    """Trích xuất ngày tháng từ text."""
    if not text:
        return None
    date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
    match = re.search(date_pattern, text)
    return match.group(0) if match else None