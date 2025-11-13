"""Article storage with category mapping"""

import json
import logging
from pathlib import Path

from src.crawling.config import ARTICLE_DIR, METADATA_DIR, CATEGORY_DIR, SUB_CATEGORY_DIR
from src.crawling.utils import create_directory, get_crawl_datetime, CategoryMapper

logger = logging.getLogger(__name__)


class ArticleStorage:
    """Manage article storage with normalized category names."""
    
    def __init__(self, base_dir):
        self.base_dir = create_directory(base_dir)
        self.category_counters = {}
        self.category_mapper = CategoryMapper()
        logger.info(f"ArticleStorage initialized: {base_dir}")
    
    def _get_next_index(self, category, subcategory=None):
        """Get next article index."""
        key = f"{category}::{subcategory}" if subcategory else category
        if key not in self.category_counters:
            self.category_counters[key] = 0
        self.category_counters[key] += 1
        return self.category_counters[key]
    
    def save_article(self, article_content, title, url, metadata, category, subcategory=None):
        """Save article with normalized category names."""
        try:
            # Normalize names
            category_normalized = self.category_mapper.get_normalized_name(category)
            category_display = self.category_mapper.get_display_name(category_normalized)
            
            subcategory_normalized = None
            subcategory_display = None
            if subcategory:
                subcategory_normalized = self.category_mapper.get_normalized_name(subcategory)
                subcategory_display = self.category_mapper.get_display_name(subcategory_normalized)
            
            # Save mappings
            self.category_mapper.save_mappings()
            
            # Determine path
            if subcategory_normalized:
                base_path = self.base_dir / category_normalized / SUB_CATEGORY_DIR / subcategory_normalized
            else:
                base_path = self.base_dir / category_normalized / CATEGORY_DIR
            
            # Create directories
            article_dir = create_directory(base_path / ARTICLE_DIR)
            metadata_dir = create_directory(base_path / METADATA_DIR)
            
            # Get index
            index = self._get_next_index(category, subcategory)
            
            # Save article
            article_file = article_dir / f"article_{index}.txt"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(article_content)
            
            # Save metadata
            metadata_full = {
                'index': index,
                'category': category,
                'subcategory': subcategory,
                'category_normalized': category_normalized,
                'subcategory_normalized': subcategory_normalized,
                'category_display': category_display,
                'subcategory_display': subcategory_display,
                'title': title,
                'url': url,
                'crawl_date': get_crawl_datetime(),
                **metadata
            }
            
            metadata_file = metadata_dir / f"metadata_{index}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_full, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Saved article {index}: {category_normalized}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error saving article: {e}")
            return False