"""Crawling utilities"""

import re
import csv
import logging
import unicodedata
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== LOGGING ====================

def setup_logging(log_dir):
    """Setup logging configuration."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / 'crawler.log'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")
    return logger


# ==================== TEXT NORMALIZATION ====================

def remove_vietnamese_accents(text):
    """Remove Vietnamese accents."""
    if not text:
        return text
    
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    vietnamese_map = {'đ': 'd', 'Đ': 'D'}
    for viet_char, latin_char in vietnamese_map.items():
        text = text.replace(viet_char, latin_char)
    
    return text


def normalize_category_name(name):
    """Normalize category name: 'Chính trị' -> 'chinh_tri'"""
    if not name:
        return name
    
    name = name.lower()
    name = remove_vietnamese_accents(name)
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.replace(' ', '_')
    name = re.sub(r'_{2,}', '_', name)
    
    return name


# ==================== CATEGORY MAPPING ====================

class CategoryMapper:
    """Manage category name mappings."""
    
    def __init__(self, mapping_file='data/category_mapping.csv'):
        self.mapping_file = Path(mapping_file)
        self.mappings = {}
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_mappings()
    
    def load_mappings(self):
        """Load mappings from CSV."""
        if not self.mapping_file.exists():
            return
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.mappings[row['normalized_name']] = {
                        'original_name': row['original_name'],
                        'display_name': row['display_name']
                    }
            logger.info(f"Loaded {len(self.mappings)} category mappings")
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
    
    def save_mappings(self):
        """Save mappings to CSV."""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['normalized_name', 'original_name', 'display_name']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for normalized, data in sorted(self.mappings.items()):
                    writer.writerow({
                        'normalized_name': normalized,
                        'original_name': data['original_name'],
                        'display_name': data['display_name']
                    })
            logger.info(f"Saved {len(self.mappings)} mappings")
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")
    
    def add_category(self, original_name):
        """Add category mapping."""
        normalized = normalize_category_name(original_name)
        display_name = original_name.upper()
        
        self.mappings[normalized] = {
            'original_name': original_name,
            'display_name': display_name
        }
        
        return normalized
    
    def get_normalized_name(self, original):
        """Get normalized name."""
        normalized = normalize_category_name(original)
        if normalized not in self.mappings:
            self.add_category(original)
        return normalized
    
    def get_display_name(self, normalized):
        """Get display name."""
        return self.mappings.get(normalized, {}).get('display_name', normalized.upper())


# ==================== URL & FILE UTILS ====================

def normalize_url(link, base_url):
    """Normalize URL."""
    if not link:
        return None
    if link.startswith('http'):
        return link
    
    link = re.sub(r'^\.+/', '', link)
    if link.startswith('/'):
        return base_url + link
    return base_url + '/' + link


def sanitize_filename(name):
    """Sanitize filename."""
    sanitized = re.sub(r'[\x00-\x1F\\/:*?"<>|]', '_', name).strip()
    sanitized = re.sub(r'_{2,}', '_', sanitized)
    return sanitized[:100]


def create_directory(path):
    """Create directory if not exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_date_from_text(text):
    """Extract date from text."""
    if not text:
        return None
    match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', text)
    return match.group(0) if match else None


def get_crawl_datetime():
    """Get current datetime."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ==================== PRINT UTILS ====================

def print_separator():
    """Print separator."""
    print("="*80)


def print_progress(message, level=0):
    """Print progress with indentation."""
    indent = "  " * level
    print(f"{indent}{message}")