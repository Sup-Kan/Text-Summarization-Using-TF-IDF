import json
# from pathlib import Path
from src.crawling.utils import sanitize_filename, create_directory, get_logger, get_crawl_datetime
from src.crawling.config import ARTICLE_DIR, METADATA_DIR, CATEGORY_DIR, SUB_CATEGORY_DIR

class ArticleStorage:
    """Class quản lý lưu trữ bài báo."""

    def __init__(self, base_dir='data/raw'):
        self.base_dir = create_directory(base_dir)
        self.category_counters = {}
        self.logger = get_logger(__name__)
        self.logger.info(f"ArticleStorage initialized with base_dir: {base_dir}")

    def _get_counter_key(self, category, subcategory=None):
        """Tạo key để đếm số bài."""
        if subcategory:
            return f"{category}::{subcategory}"
        return category

    def _get_next_index(self, category, subcategory=None):
        """Lấy index tiếp theo cho bài báo."""
        key = self._get_counter_key(category, subcategory)
        if key not in self.category_counters:
            self.category_counters[key] = 0
        self.category_counters[key] += 1
        
        self.logger.debug(f"Next index for {key}: {self.category_counters[key]}")
        return self.category_counters[key]

    def save_article(self, article_content, title, url, metadata, category, subcategory=None):
        """
        Lưu bài báo với metadata bao gồm cả crawl_date.
        """
        try:
            self.logger.info(f"Saving article: category={category}, subcategory={subcategory}")
            
            category_clean = sanitize_filename(category)

            # Xác định đường dẫn
            if subcategory:
                subcategory_clean = sanitize_filename(subcategory)
                base_path = self.base_dir / category_clean / SUB_CATEGORY_DIR / subcategory_clean
                self.logger.debug(f"Subcategory path: {base_path}")
            else:
                base_path = self.base_dir / category_clean / CATEGORY_DIR
                self.logger.debug(f"Category path: {base_path}")

            # Tạo thư mục
            article_dir = create_directory(base_path / ARTICLE_DIR)
            metadata_dir = create_directory(base_path / METADATA_DIR)
            
            self.logger.debug(f"Created directories: article, metadata")

            # Lấy index
            index = self._get_next_index(category, subcategory)

            # === 1. LƯU ARTICLE ===
            article_filepath = article_dir / f"article_{index}.txt"
            with open(article_filepath, 'w', encoding='utf-8') as f:
                f.write(article_content)
            self.logger.debug(f"Saved article to: {article_filepath}")

            # === 2. LƯU METADATA (với crawl_date) ===
            metadata_filepath = metadata_dir / f"metadata_{index}.json"
            metadata_full = {
                'index': index,
                'category': category,
                'subcategory': subcategory,
                'title': title,
                'url': url,
                'date': metadata.get('date'),  # Ngày đăng bài
                'author': metadata.get('author'),
                'source': metadata.get('source', 'baochinhphu.vn'),
                'crawl_date': get_crawl_datetime()  # Thời gian crawl
            }
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata_full, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved metadata to: {metadata_filepath}")

            # Log success
            rel_path = base_path.relative_to(self.base_dir)
            self.logger.info(f"✓ Successfully saved article {index}: {rel_path}")
            print(f"      ✓ Đã lưu: {rel_path}/[article|metadata]_{index}")
            
            return True

        except Exception as e:
            self.logger.error(f"✗ Error saving article: {e}", exc_info=True)
            print(f"      ✗ Lỗi khi lưu file: {e}")
            return False

    def get_stats(self):
        """Lấy thống kê về dữ liệu đã lưu."""
        self.logger.info("Getting storage statistics")
        
        categories = [d for d in self.base_dir.iterdir() if d.is_dir()]
        total_subcategories = 0
        total_articles = 0

        for category_dir in categories:
            # Đếm bài trong category chính
            main_article_dir = category_dir / CATEGORY_DIR / ARTICLE_DIR
            if main_article_dir.exists():
                articles = [f for f in main_article_dir.iterdir() if f.is_file()]
                total_articles += len(articles)
                self.logger.debug(f"Category {category_dir.name}: {len(articles)} articles")

            # Đếm subcategories
            sub_category_base_dir = category_dir / SUB_CATEGORY_DIR
            if sub_category_base_dir.exists():
                subdirs = [d for d in sub_category_base_dir.iterdir() if d.is_dir()]
                total_subcategories += len(subdirs)

                for subcat_dir in subdirs:
                    subcat_article_dir = subcat_dir / ARTICLE_DIR
                    if subcat_article_dir.exists():
                        articles = [f for f in subcat_article_dir.iterdir() if f.is_file()]
                        total_articles += len(articles)
                        self.logger.debug(f"Subcategory {subcat_dir.name}: {len(articles)} articles")

        stats = {
            'categories': len(categories),
            'subcategories': total_subcategories,
            'articles': total_articles
        }
        
        self.logger.info(f"Storage stats: {stats}")
        return stats