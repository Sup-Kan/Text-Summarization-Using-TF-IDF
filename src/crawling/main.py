"""Main crawler entry point"""

import sys
import time
import argparse
from pathlib import Path

from src.crawling.config import *
from src.crawling.utils import setup_logging, print_separator, print_progress
from src.crawling.storage import ArticleStorage
from src.crawling.scraper import NewsScraper


def main(max_categories=None, max_subcategories=None, max_articles=None):
    """Main crawler function."""
    
    # Setup logging
    logger = setup_logging(LOG_DIR)
    
    # Config
    max_categories = max_categories or DEFAULT_MAX_CATEGORIES
    max_subcategories = max_subcategories or DEFAULT_MAX_SUBCATEGORIES
    max_articles = max_articles or DEFAULT_MAX_ARTICLES
    
    crawl_date = get_today()
    
    print_separator()
    print(f"📅 NGÀY CRAWL: {crawl_date}")
    print_separator()
    print(f"Cấu hình:")
    print(f"  - Max categories: {max_categories}")
    print(f"  - Max subcategories: {max_subcategories}")
    print(f"  - Max articles: {max_articles}")
    print(f"  - Output: {OUTPUT_DIR}")
    print_separator()
    
    try:
        # Initialize
        storage = ArticleStorage(OUTPUT_DIR)
        scraper = NewsScraper(storage)
        
        # Get categories
        categories = scraper.get_main_categories()
        if not categories:
            print("✗ Không tìm thấy chuyên mục!")
            return
        
        if max_categories:
            categories = categories[:max_categories]
        
        # Crawl
        total_stats = {'categories': 0, 'subcategories': 0, 'articles': 0}
        
        for idx, category in enumerate(categories, 1):
            print_separator()
            print(f"📁 CHUYÊN MỤC {idx}/{len(categories)}: {category['title']}")
            print_separator()
            
            stats = scraper.crawl_category(category, max_subcategories, max_articles)
            
            total_stats['categories'] += 1
            total_stats['subcategories'] += stats['subcategories']
            total_stats['articles'] += stats['articles']
            
            time.sleep(DELAY_BETWEEN_CATEGORIES)
        
        # Results
        print_separator()
        print("✅ HOÀN THÀNH!")
        print_separator()
        print(f"✓ Đã crawl {total_stats['categories']} chuyên mục")
        print(f"✓ Đã crawl {total_stats['subcategories']} chuyên mục con")
        print(f"✓ Đã lưu {total_stats['articles']} bài báo")
        print(f"✓ Dữ liệu: {OUTPUT_DIR}")
        print_separator()
        
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        print(f"\n✗ LỖI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()