"""
Main processor for batch text summarization with VnCoreNLP
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from src.preprocessing.config import *
# from src.preprocessing.vncorenlp_setup import setup_vncorenlp
from src.preprocessing.sentence_tokenizer import SentenceTokenizer
from src.preprocessing.tfidf_summarizer import TfidfSummarizer
from src.preprocessing.stopwords_loader import StopwordsLoader

logger = logging.getLogger(__name__)


class TextProcessor:
    """Process articles and generate summaries using VnCoreNLP."""
    
    def __init__(self, raw_data_dir, processed_data_dir, vncorenlp_dir, 
                 stopwords_file, num_sentences=3):
        """
        Initialize processor.
        
        Args:
            raw_data_dir: Path to raw data
            processed_data_dir: Path to save processed data
            vncorenlp_dir: Path to VnCoreNLP installation
            stopwords_file: Path to stopwords file
            num_sentences: Number of sentences in summary
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.vncorenlp_dir = vncorenlp_dir
        self.num_sentences = num_sentences
        
        # Load stopwords
        logger.info("Loading stopwords...")
        stopwords_loader = StopwordsLoader(stopwords_file)
        self.stopwords = stopwords_loader.get_stopwords()
        
        # Initialize components
        logger.info("Initializing NLP components...")
        self.sentence_tokenizer = SentenceTokenizer(
            vncorenlp_dir=vncorenlp_dir,
            min_length=MIN_SENTENCE_LENGTH,
            max_length=MAX_SENTENCE_LENGTH
        )
        self.summarizer = TfidfSummarizer(
            vncorenlp_dir=vncorenlp_dir,
            stopwords=self.stopwords,
            num_sentences=num_sentences,
            use_idf=USE_IDF,
            smooth_idf=SMOOTH_IDF
        )
        
        logger.info(f"TextProcessor initialized")
        logger.info(f"  Raw data: {self.raw_data_dir}")
        logger.info(f"  Processed data: {self.processed_data_dir}")
        logger.info(f"  Stopwords: {len(self.stopwords)}")
    
    def _create_output_dirs(self, category_path):
        """Create output directories for a category."""
        summary_dir = category_path / SUMMARY_DIR
        metadata_dir = category_path / METADATA_DIR
        sentences_dir = category_path / SENTENCES_DIR
        
        summary_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        sentences_dir.mkdir(parents=True, exist_ok=True)
        
        return summary_dir, metadata_dir, sentences_dir
    
    def process_article(self, article_path, metadata_path, output_paths):
        """
        Process a single article.
        
        Args:
            article_path: Path to article file
            metadata_path: Path to metadata file
            output_paths: Tuple of (summary_dir, metadata_dir, sentences_dir)
        
        Returns:
            bool: Success status
        """
        summary_dir, metadata_dir, sentences_dir = output_paths
        
        try:
            # Read article
            with open(article_path, 'r', encoding='utf-8') as f:
                article_text = f.read()
            
            # Read metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            article_id = metadata['index']
            logger.info(f"Processing article {article_id}: {metadata['title'][:50]}...")
            
            # === STEP 1: Sentence tokenization with VnCoreNLP ===
            sentences = self.sentence_tokenizer.tokenize(article_text)
            
            if not sentences:
                logger.warning(f"No sentences extracted from article {article_id}")
                return False
            
            logger.debug(f"Extracted {len(sentences)} sentences")
            
            # === STEP 2: Summarization with TF-IDF ===
            summary_result = self.summarizer.summarize(sentences)
            
            if not summary_result['summary']:
                logger.warning(f"Failed to generate summary for article {article_id}")
                return False
            
            summary_text = ' '.join(summary_result['summary'])
            logger.info(f"Generated summary: {len(summary_result['summary'])} sentences")
            
            # === STEP 3: Save outputs ===
            
            # Save summary
            summary_file = summary_dir / f"summary_{article_id}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            logger.debug(f"Saved summary: {summary_file}")
            
            # Save sentences (for debugging)
            sentences_file = sentences_dir / f"sentences_{article_id}.json"
            with open(sentences_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'sentences': sentences,
                    'selected_indices': summary_result['indices'],
                    'scores': summary_result['scores']
                }, f, ensure_ascii=False, indent=2)
            
            # Update metadata
            metadata['summary_method'] = 'tfidf-vncorenlp'
            metadata['summary_sentences_count'] = len(summary_result['summary'])
            metadata['summary_selected_indices'] = summary_result['indices']
            metadata['processing_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata['vncorenlp_version'] = '1.2'
            
            metadata_file = metadata_dir / f"metadata_{article_id}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved metadata: {metadata_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing article: {e}", exc_info=True)
            return False
    
    def process_category(self, category_name, is_subcategory=False, subcategory_name=None):
        """
        Process all articles in a category.
        
        Args:
            category_name: Category name
            is_subcategory: Whether this is a subcategory
            subcategory_name: Subcategory name if applicable
        
        Returns:
            dict: Statistics
        """
        stats = {'processed': 0, 'failed': 0}
        
        # Determine paths
        if is_subcategory:
            raw_category_path = self.raw_data_dir / category_name / SUB_CATEGORY_DIR / subcategory_name
            processed_category_path = self.processed_data_dir / category_name / SUB_CATEGORY_DIR / subcategory_name
            logger.info(f"Processing subcategory: {category_name}/{subcategory_name}")
        else:
            raw_category_path = self.raw_data_dir / category_name / CATEGORY_DIR
            processed_category_path = self.processed_data_dir / category_name / CATEGORY_DIR
            logger.info(f"Processing category: {category_name}")
        
        # Check if input exists
        article_dir = raw_category_path / ARTICLE_DIR
        metadata_dir = raw_category_path / METADATA_DIR
        
        if not article_dir.exists():
            logger.warning(f"Article directory not found: {article_dir}")
            return stats
        
        # Create output directories
        output_paths = self._create_output_dirs(processed_category_path)
        
        # Process each article
        article_files = sorted(article_dir.glob('article_*.txt'))
        
        for article_file in article_files:
            # Get corresponding metadata
            article_id = article_file.stem.split('_')[1]
            metadata_file = metadata_dir / f"metadata_{article_id}.json"
            
            if not metadata_file.exists():
                logger.warning(f"Metadata not found for article {article_id}")
                stats['failed'] += 1
                continue
            
            # Process
            success = self.process_article(article_file, metadata_file, output_paths)
            
            if success:
                stats['processed'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"Category stats: {stats}")
        return stats
    
    def process_all(self):
        """
        Process all categories and subcategories.
        
        Returns:
            dict: Overall statistics
        """
        total_stats = {'categories': 0, 'subcategories': 0, 'processed': 0, 'failed': 0}
        
        logger.info("Starting batch processing")
        
        # Iterate through all categories
        for category_dir in self.raw_data_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            category_name = category_dir.name
            logger.info(f"Processing category: {category_name}")
            
            # Process main category
            category_stats = self.process_category(category_name, is_subcategory=False)
            total_stats['categories'] += 1
            total_stats['processed'] += category_stats['processed']
            total_stats['failed'] += category_stats['failed']
            
            # Process subcategories
            sub_category_dir = category_dir / SUB_CATEGORY_DIR
            if sub_category_dir.exists():
                for subcat_dir in sub_category_dir.iterdir():
                    if subcat_dir.is_dir():
                        subcategory_name = subcat_dir.name
                        
                        subcat_stats = self.process_category(
                            category_name,
                            is_subcategory=True,
                            subcategory_name=subcategory_name
                        )
                        
                        total_stats['subcategories'] += 1
                        total_stats['processed'] += subcat_stats['processed']
                        total_stats['failed'] += subcat_stats['failed']
        
        logger.info(f"Batch processing completed: {total_stats}")
        return total_stats
    
    def cleanup(self):
        """Close VnCoreNLP connections."""
        logger.info("Cleaning up VnCoreNLP resources...")
        self.sentence_tokenizer.close()
        self.summarizer.close()
        logger.info("Cleanup completed")