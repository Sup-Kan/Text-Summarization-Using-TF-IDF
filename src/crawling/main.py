"""
Main entry point for news crawler
"""

import time
import sys
# from pathlib import Path

# Uncomment when using as separate modules
from src.crawling.config import BASE_DATA_DIR, LOG_DIR, OUTPUT_DIR, DEFAULT_MAX_CATEGORIES, DEFAULT_MAX_SUBCATEGORIES, DEFAULT_MAX_ARTICLES, DELAY_BETWEEN_CATEGORIES
from src.crawling.utils import setup_logging, print_separator, print_progress
from src.crawling.utils import create_latest_symlink, get_crawl_date
from src.crawling.storage import ArticleStorage
from src.crawling.scraper import NewsScraper

def main(max_categories=None, max_subcategories=None, max_articles=None):
    """Hàm chính để crawl tin tức."""
    
    # ============================================
    # BƯỚC 1: HIỂN thị thông tin ngày crawl
    # ============================================
    crawl_date = get_crawl_date()
    print_separator()
    print(f"📅 NGÀY CRAWL: {crawl_date}")
    print_separator()
    print()
    
    # ============================================
    # BƯỚC 2: SETUP LOGGING
    # ============================================
    try:
        logger = setup_logging(LOG_DIR)
        logger.info("=" * 80)
        logger.info(f"NEWS CRAWLER STARTED - DATE: {crawl_date}")
        logger.info("=" * 80)
    except Exception as e:
        print(f"CRITICAL: Failed to setup logging: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Use defaults
    max_categories = max_categories or DEFAULT_MAX_CATEGORIES
    max_subcategories = max_subcategories or DEFAULT_MAX_SUBCATEGORIES
    max_articles = max_articles or DEFAULT_MAX_ARTICLES

    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  - Crawl date: {crawl_date}")
    logger.info(f"  - Max categories: {max_categories or 'ALL'}")
    logger.info(f"  - Max subcategories: {max_subcategories or 'ALL'}")
    logger.info(f"  - Max articles: {max_articles or 'ALL'}")
    logger.info(f"  - Output directory: {OUTPUT_DIR}")
    logger.info(f"  - Log directory: {LOG_DIR}")

    print("BẮT ĐẦU CRAWL WEBSITE BAOCHINHPHU.VN")
    print_separator()
    print(f"Cấu hình:")
    print(f"  - Ngày crawl: {crawl_date}")
    print(f"  - Số chuyên mục tối đa: {max_categories or 'TẤT CẢ'}")
    print(f"  - Số chuyên mục con tối đa: {max_subcategories or 'TẤT CẢ'}")
    print(f"  - Số bài báo/chuyên mục: {max_articles or 'TẤT CẢ'}")
    print(f"  - Thư mục lưu: {OUTPUT_DIR}")
    print(f"  - Thư mục log: {LOG_DIR}")
    print_separator()
    print()

    try:
        # Initialize storage and scraper
        logger.info("Initializing storage and scraper")
        storage = ArticleStorage(OUTPUT_DIR)
        scraper = NewsScraper(storage)

        # Get main categories
        logger.info("Starting to fetch categories")
        categories = scraper.get_main_categories()

        if not categories:
            logger.warning("No categories found!")
            print("✗ Không tìm thấy chuyên mục nào!")
            return

        # Apply limit
        if max_categories:
            categories = categories[:max_categories]
            logger.info(f"Limited to {max_categories} categories")

        print()

        # Crawl each category
        total_stats = {'categories': 0, 'subcategories': 0, 'articles': 0}

        for cat_idx, category in enumerate(categories, 1):
            print_separator()
            print(f"📁 CHUYÊN MỤC {cat_idx}/{len(categories)}: {category['title']}")
            print_separator()
            
            logger.info(f"Processing category {cat_idx}/{len(categories)}: {category['title']}")

            try:
                stats = scraper.crawl_category(category, max_subcategories, max_articles)

                total_stats['categories'] += 1
                total_stats['subcategories'] += stats['subcategories']
                total_stats['articles'] += stats['articles']

                print_progress(f"✓ Hoàn thành: {stats['subcategories']} chuyên mục con, {stats['articles']} bài báo")
                logger.info(f"Completed category {category['title']}: {stats}")

            except Exception as e:
                logger.error(f"Error processing category {category['title']}: {e}", exc_info=True)
                print_progress(f"✗ Lỗi khi xử lý chuyên mục: {e}", level=1)
                continue

            time.sleep(DELAY_BETWEEN_CATEGORIES)

        # ============================================
        # BƯỚC 3: TẠO SYMLINK 'latest'
        # ============================================
        try:
            create_latest_symlink(BASE_DATA_DIR, crawl_date)
        except Exception as e:
            logger.warning(f"Could not create symlink: {e}")

        # Print results
        print()
        print_separator()
        print("HOÀN THÀNH CRAWL!")
        print_separator()
        print(f"📅 Ngày crawl: {crawl_date}")
        print(f"✅ Đã xử lý {total_stats['categories']} chuyên mục chính")
        print(f"✅ Đã xử lý {total_stats['subcategories']} chuyên mục con")
        print(f"✅ Đã lưu {total_stats['articles']} bài báo")
        print(f"✅ Dữ liệu được lưu trong: {OUTPUT_DIR}")
        print(f"✅ Log được lưu trong: {LOG_DIR}")
        print(f"✅ Symlink 'latest': {BASE_DATA_DIR}/latest -> {crawl_date}")
        print_separator()

        logger.info("=" * 80)
        logger.info("CRAWLING COMPLETED SUCCESSFULLY")
        logger.info(f"Final stats: {total_stats}")
        logger.info("=" * 80)

    except Exception as e:
        logger.critical(f"CRITICAL ERROR in main: {e}", exc_info=True)
        print(f"\n✗ LỖI NGHIÊM TRỌNG: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()