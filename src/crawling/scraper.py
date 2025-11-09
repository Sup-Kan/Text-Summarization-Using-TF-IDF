import requests
from bs4 import BeautifulSoup
import re
import time
from src.crawling.config import HEADERS, REQUEST_TIMEOUT, URL, MAX_RETRIES, RETRY_DELAY
from src.crawling.config import DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_SUBCATEGORIES
from src.crawling.config import EXCLUDED_CATEGORIES
from src.crawling.utils import normalize_url, print_progress, retry, get_logger
from src.crawling.utils import extract_date_from_text

class NewsScraper:
    """Class chính để crawl tin tức."""

    def __init__(self, storage):
        self.storage = storage
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.logger = get_logger(__name__)
        self.logger.info("NewsScraper initialized")

    @retry(max_attempts=MAX_RETRIES, delay=RETRY_DELAY, exceptions=(requests.RequestException,))
    def _make_request(self, url):
        """Thực hiện HTTP request với retry."""
        try:
            self.logger.debug(f"Requesting URL: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.debug(f"✓ Request successful: {url} (status={response.status_code})")
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            self.logger.error(f"✗ Request failed for {url}: {e}")
            raise

    def get_main_categories(self):
        """Lấy danh sách các chuyên mục chính."""
        print_progress("Đang lấy danh sách chuyên mục chính...")
        self.logger.info("Fetching main categories from homepage")

        soup = self._make_request(URL)
        if not soup:
            self.logger.warning("No soup returned from homepage")
            return []

        main_menu = soup.find('div', class_='header__menu')
        if not main_menu:
            self.logger.warning("Main menu not found on homepage")
            return []

        menu_items = main_menu.find('ul').find_all('li', recursive=False)
        categories = []

        for li in menu_items:
            anchor_tag = li.find('a', class_='nav-link') or li.find('a')

            if anchor_tag:
                title = anchor_tag.get_text(strip=True)
                link = anchor_tag.get('href')

                if title and link and title.lower() not in EXCLUDED_CATEGORIES:
                    full_link = normalize_url(link, URL)
                    categories.append({
                        'title': title,
                        'link': full_link
                    })
                    self.logger.info(f"Found category: {title} ({full_link})")

        self.logger.info(f"Total categories found: {len(categories)}")
        print_progress(f"✓ Tìm thấy {len(categories)} chuyên mục chính", level=1)
        return categories

    def get_subcategories_from_category(self, category_url):
        """Lấy các chuyên mục con từ breadcrumb."""
        print_progress(f"→ Đang lấy chuyên mục con...", level=1)

        soup = self._make_request(category_url)
        if not soup:
            return []

        subcategories = []
        breadcrumb = soup.find('div', class_='list__breadcrumb')
        
        if breadcrumb:
            breadcrumb_ul = breadcrumb.find('ul')
            if breadcrumb_ul:
                breadcrumb_items = breadcrumb_ul.find_all('li')

                for li in breadcrumb_items:
                    h1_tag = li.find('h1')
                    sub_anchor = h1_tag.find('a') if h1_tag else li.find('a')

                    if sub_anchor:
                        sub_title = sub_anchor.get_text(strip=True)
                        sub_link = sub_anchor.get('href')

                        if sub_title and sub_link and sub_link not in ['/', category_url]:
                            full_link = normalize_url(sub_link, URL)

                            if not any(s['link'] == full_link for s in subcategories):
                                subcategories.append({
                                    'title': sub_title,
                                    'link': full_link
                                })
                                self.logger.info(f"Found subcategory: {sub_title}")

        print_progress(f"✓ Tìm thấy {len(subcategories)} chuyên mục con", level=2)
        return subcategories

    def get_articles_from_page(self, page_url, max_articles=10):
        """Lấy các bài báo từ trang."""
        print_progress(f"→ Đang lấy bài báo...", level=2)

        soup = self._make_request(page_url)
        if not soup:
            return []

        articles = []
        seen_links = set()

        # Strategy 1: Find in h2 and h3
        title_tags = soup.find_all(['h2', 'h3'])
        
        for tag in title_tags:
            link_tag = tag.find('a', href=re.compile(r'\.htm$'))
            if link_tag:
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href')
                
                if title and link:
                    full_link = normalize_url(link, URL)
                    
                    if full_link not in seen_links:
                        seen_links.add(full_link)
                        articles.append({
                            'title': title,
                            'link': full_link
                        })

        # Strategy 2: Find by common classes (fallback)
        if not articles:
            article_links = soup.find_all('a', {
                'href': re.compile(r'\.htm$'),
                'class': re.compile(r'box-category-link-title|title-news|article-title', re.I)
            })
            
            for link_tag in article_links:
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href')
                
                if title and link:
                    full_link = normalize_url(link, URL)
                    
                    if full_link not in seen_links:
                        seen_links.add(full_link)
                        articles.append({
                            'title': title,
                            'link': full_link
                        })

        # Apply limit
        if max_articles:
            articles = articles[:max_articles]

        print_progress(f"✓ Tìm thấy {len(articles)} bài báo", level=3)
        self.logger.info(f"Found {len(articles)} articles on {page_url}")
        return articles

    def _extract_author_from_paragraphs(self, paragraphs):
        """
        Trích xuất tác giả từ thẻ <p> cuối cùng.
        Thường là: <p><b>Tên tác giả</b></p>
        
        Returns:
            tuple: (author_name, paragraphs_without_author)
        """
        if not paragraphs:
            return None, paragraphs
        
        # Kiểm tra thẻ <p> cuối cùng
        last_p = paragraphs[-1]
        
        # Tìm thẻ <b> trong <p> cuối
        b_tag = last_p.find('b')
        
        if b_tag:
            author_text = b_tag.get_text(strip=True)
            
            # Validate: không chứa các từ khóa không phải tên
            # (tránh nhầm với in đậm bình thường)
            invalid_keywords = ['nguồn', 'theo', 'tham khảo', 'xem thêm', 'liên hệ']
            
            if author_text and len(author_text) < 50:  # Tên không quá dài
                is_valid = True
                for keyword in invalid_keywords:
                    if keyword in author_text.lower():
                        is_valid = False
                        break
                
                if is_valid:
                    self.logger.info(f"Extracted author: {author_text}")
                    # Loại bỏ thẻ <p> cuối khỏi danh sách
                    return author_text, paragraphs[:-1]
        
        return None, paragraphs

    def get_article_content(self, article_url, article_title):
        """
        Lấy nội dung đầy đủ + metadata.
        QUAN TRỌNG: Trích xuất tác giả và loại bỏ khỏi nội dung.
        
        Returns:
            tuple: (content, metadata_dict)
        """
        soup = self._make_request(article_url)
        if not soup:
            return None, {}

        # === 1. Lấy NỘI DUNG CHÍNH ===
        content_div = soup.find('div', class_='detail-content')
        
        if not content_div:
            self.logger.warning(f"No content div found for {article_url}")
            return None, {}
        
        # Lấy tất cả các thẻ p, h2, h3
        paragraphs = content_div.find_all(['p', 'h2', 'h3'])
        
        if not paragraphs:
            self.logger.warning(f"No paragraphs found in content div for {article_url}")
            return None, {}

        # === 2. TRÍCH XUẤT TÁC GIẢ VÀ LOẠI BỎ KHỎI NỘI DUNG ===
        author, cleaned_paragraphs = self._extract_author_from_paragraphs(paragraphs)
        
        # Ghép nội dung (đã loại bỏ tác giả)
        content_parts = [p.get_text(strip=True) for p in cleaned_paragraphs if p.get_text(strip=True)]
        main_content = '\n\n'.join(content_parts) if content_parts else ""

        # === 3. TRÍCH XUẤT METADATA ===
        metadata = {
            'date': None,
            'author': author,  # Đã trích xuất ở trên
            'source': 'baochinhphu.vn'
        }

        # Tìm ngày đăng
        detail_time = soup.find('div', class_='detail-time') or soup.find('span', class_='time')
        if detail_time:
            date_text = detail_time.get_text(strip=True)
            metadata['date'] = extract_date_from_text(date_text)
            self.logger.debug(f"Extracted date: {metadata['date']}")

        # Fallback: tìm ngày trong breadcrumb hoặc meta tags
        if not metadata['date']:
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date:
                metadata['date'] = meta_date.get('content', '')[:10]  # YYYY-MM-DD

        self.logger.info(f"Extracted metadata: author={metadata['author']}, date={metadata['date']}")

        return main_content, metadata

    def crawl_category(self, category, max_subcategories, max_articles):
        """Crawl một chuyên mục hoàn chỉnh."""
        stats = {'subcategories': 0, 'articles': 0}

        # 1. Crawl category chính
        print_progress("📂 Crawl bài từ chuyên mục chính...", level=1)
        main_articles = self.get_articles_from_page(category['link'], max_articles)

        for article_idx, article in enumerate(main_articles, 1):
            print_progress(f"📄 Bài {article_idx}/{len(main_articles)}: {article['title'][:50]}...", level=2)

            content, metadata = self.get_article_content(article['link'], article['title'])

            if content:
                success = self.storage.save_article(
                    article_content=content,
                    title=article['title'],
                    url=article['link'],
                    metadata=metadata,
                    category=category['title'],
                    subcategory=None
                )

                if success:
                    stats['articles'] += 1

            time.sleep(DELAY_BETWEEN_REQUESTS)

        # 2. Lấy subcategories
        subcategories = self.get_subcategories_from_category(category['link'])
        
        if max_subcategories:
            subcategories = subcategories[:max_subcategories]

        # 3. Crawl subcategories
        for sub_idx, subcategory in enumerate(subcategories, 1):
            print_progress(f"📁 Chuyên mục con {sub_idx}/{len(subcategories)}: {subcategory['title']}", level=1)

            sub_articles = self.get_articles_from_page(subcategory['link'], max_articles)

            for article_idx, article in enumerate(sub_articles, 1):
                print_progress(f"📄 Bài {article_idx}/{len(sub_articles)}: {article['title'][:50]}...", level=2)

                content, metadata = self.get_article_content(article['link'], article['title'])

                if content:
                    success = self.storage.save_article(
                        article_content=content,
                        title=article['title'],
                        url=article['link'],
                        metadata=metadata,
                        category=category['title'],
                        subcategory=subcategory['title']
                    )

                    if success:
                        stats['articles'] += 1

                time.sleep(DELAY_BETWEEN_REQUESTS)

            if sub_articles:
                stats['subcategories'] += 1

            time.sleep(DELAY_BETWEEN_SUBCATEGORIES)

        return stats