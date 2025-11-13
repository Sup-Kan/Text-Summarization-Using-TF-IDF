"""Web scraper with multi-selector support"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from functools import wraps

from src.crawling.config import *
from src.crawling.utils import normalize_url, print_progress, extract_date_from_text

logger = logging.getLogger(__name__)


def retry(max_attempts=3, delay=5):
    """Retry decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


class NewsScraper:
    """News scraper with multi-selector fallback."""
    
    def __init__(self, storage):
        self.storage = storage
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Multi-selector definitions
        self.thumbnail_selectors = [
            'div.box-category-item img',
            'div.box-stream img',
            'div.timeline_list img',
            'div[class*="box"] img'
        ]
        
        self.sapo_selectors = [
            'div.box-category-item p',
            'div.box-stream p',
            'div.timeline_list p',
            'p.sapo'
        ]
        
        self.time_selectors = [
            'span.time',
            'span.date',
            'div.time'
        ]
        
        logger.info("NewsScraper initialized")
    
    @retry(max_attempts=MAX_RETRIES, delay=RETRY_DELAY)
    def _make_request(self, url):
        """Make HTTP request with retry."""
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def _extract_with_fallback(self, element, selectors, is_image=False):
        """Extract content using multiple selectors."""
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    if is_image:
                        content = found.get('src') or found.get('data-src')
                        if content:
                            return normalize_url(content, URL)
                    else:
                        text = found.get_text(separator=' ', strip=True)
                        return ' '.join(text.split()) if text else None
            except:
                continue
        return None
    
    def get_main_categories(self):
        """Get main categories."""
        print_progress("Đang lấy danh sách chuyên mục chính...")
        
        soup = self._make_request(URL)
        main_menu = soup.find('div', class_='header__menu')
        
        if not main_menu:
            return []
        
        categories = []
        menu_items = main_menu.find('ul').find_all('li', recursive=False)
        
        for li in menu_items:
            anchor = li.find('a', class_='nav-link') or li.find('a')
            if anchor:
                title = anchor.get_text(strip=True)
                link = anchor.get('href')
                
                if title and link and title.lower() not in EXCLUDED_CATEGORIES:
                    categories.append({
                        'title': title,
                        'link': normalize_url(link, URL)
                    })
        
        print_progress(f"✓ Tìm thấy {len(categories)} chuyên mục", level=1)
        return categories
    
    def get_subcategories(self, category_url):
        """Get subcategories from breadcrumb."""
        soup = self._make_request(category_url)
        breadcrumb = soup.find('div', class_='list__breadcrumb')
        
        if not breadcrumb:
            return []
        
        subcategories = []
        seen = set()
        
        for li in breadcrumb.find_all('li'):
            anchor = li.find('a')
            if anchor:
                title = anchor.get_text(strip=True)
                link = anchor.get('href')
                
                if title and link and link not in ['/', category_url]:
                    full_link = normalize_url(link, URL)
                    if full_link not in seen:
                        seen.add(full_link)
                        subcategories.append({'title': title, 'link': full_link})
        
        return subcategories
    
    def get_articles_from_page(self, page_url, max_articles=10):
        """Get articles with metadata using multi-selector."""
        soup = self._make_request(page_url)
        articles = []
        seen = set()
        
        # Find article containers
        containers = soup.select('div[class*="box-category"], div[class*="box-stream"], div.timeline_list > div')
        
        for box in containers[:max_articles * 2]:
            try:
                link_tag = box.find('a', href=re.compile(r'\.htm$'))
                if not link_tag:
                    continue
                
                # Title
                title_tag = box.find(['h2', 'h3']) or link_tag
                title = title_tag.get_text(separator=' ', strip=True)
                title = ' '.join(title.split())
                
                # URL
                link = normalize_url(link_tag.get('href'), URL)
                
                if not title or not link or link in seen:
                    continue
                
                seen.add(link)
                
                # Extract metadata with fallback
                thumbnail = self._extract_with_fallback(box, self.thumbnail_selectors, is_image=True)
                sapo = self._extract_with_fallback(box, self.sapo_selectors)
                published_time = self._extract_with_fallback(box, self.time_selectors)
                
                articles.append({
                    'title': title,
                    'link': link,
                    'thumbnail': thumbnail,
                    'sapo': sapo,
                    'published_time': published_time
                })
                
                if len(articles) >= max_articles:
                    break
                    
            except Exception as e:
                logger.warning(f"Error extracting article: {e}")
                continue
        
        print_progress(f"✓ Tìm thấy {len(articles)} bài báo", level=3)
        return articles
    
    def get_article_content(self, article_url):
        """Get article full content and metadata."""
        soup = self._make_request(article_url)
        content_div = soup.find('div', class_='detail-content')
        
        if not content_div:
            return None, {}
        
        # Remove unwanted elements
        for tag in content_div.find_all(['figure', 'figcaption', 'script', 'style', 'iframe']):
            tag.decompose()
        
        # Get paragraphs
        paragraphs = content_div.find_all(['p', 'h2', 'h3'])
        
        if not paragraphs:
            return None, {}
        
        # Extract author from last <p><b>
        author = None
        if paragraphs:
            last_p = paragraphs[-1]
            b_tag = last_p.find('b')
            if b_tag:
                author_text = b_tag.get_text(separator=' ', strip=True)
                if len(author_text) < 50 and not any(kw in author_text.lower() for kw in ['nguồn', 'ảnh', 'theo']):
                    author = author_text
                    paragraphs = paragraphs[:-1]
        
        # Build content
        content_parts = []
        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            
            # Filter image captions
            if text and len(text) > 20:
                if not any(kw in text.lower()[:50] for kw in ['ảnh:', 'nguồn:', 'hình:']):
                    content_parts.append(text)
        
        main_content = '\n'.join(content_parts)
        
        # Extract metadata
        metadata = {
            'author': author,
            'source': 'baochinhphu.vn',
            'date': None,
            'published_time': None
        }
        
        # Date
        detail_time = soup.find('div', class_='detail-time') or soup.find('span', class_='time')
        if detail_time:
            date_text = detail_time.get_text(separator=' ', strip=True)
            metadata['date'] = extract_date_from_text(date_text)
            metadata['published_time'] = date_text
        
        # Featured image
        img_tag = soup.select_one('div.detail-content img, div.detail-image img')
        if img_tag:
            metadata['featured_image'] = normalize_url(img_tag.get('src') or img_tag.get('data-src'), URL)
        
        return main_content, metadata
    
    def crawl_category(self, category, max_subcategories, max_articles):
        """Crawl complete category."""
        stats = {'subcategories': 0, 'articles': 0}
        
        # Main category
        print_progress("📂 Crawl chuyên mục chính...", level=1)
        articles = self.get_articles_from_page(category['link'], max_articles)
        
        for idx, article in enumerate(articles, 1):
            print_progress(f"📄 Bài {idx}/{len(articles)}: {article['title'][:50]}...", level=2)
            
            content, metadata = self.get_article_content(article['link'])
            
            if content:
                full_metadata = {**metadata, **article}
                success = self.storage.save_article(
                    article_content=content,
                    title=article['title'],
                    url=article['link'],
                    metadata=full_metadata,
                    category=category['title'],
                    subcategory=None
                )
                if success:
                    stats['articles'] += 1
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Subcategories
        subcategories = self.get_subcategories(category['link'])
        if max_subcategories:
            subcategories = subcategories[:max_subcategories]
        
        for sub in subcategories:
            print_progress(f"📁 Chuyên mục con: {sub['title']}", level=1)
            
            sub_articles = self.get_articles_from_page(sub['link'], max_articles)
            
            for idx, article in enumerate(sub_articles, 1):
                print_progress(f"📄 Bài {idx}/{len(sub_articles)}: {article['title'][:50]}...", level=2)
                
                content, metadata = self.get_article_content(article['link'])
                
                if content:
                    full_metadata = {**metadata, **article}
                    success = self.storage.save_article(
                        article_content=content,
                        title=article['title'],
                        url=article['link'],
                        metadata=full_metadata,
                        category=category['title'],
                        subcategory=sub['title']
                    )
                    if success:
                        stats['articles'] += 1
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
            
            if sub_articles:
                stats['subcategories'] += 1
            
            time.sleep(DELAY_BETWEEN_SUBCATEGORIES)
        
        return stats