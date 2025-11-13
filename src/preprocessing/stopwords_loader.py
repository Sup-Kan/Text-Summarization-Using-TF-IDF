import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StopwordsLoader:
    """Load and manage Vietnamese stopwords."""
    
    def __init__(self, stopwords_file=None):
        """
        Initialize loader.
        
        Args:
            stopwords_file: Path to stopwords file
        """
        self.stopwords_file = stopwords_file
        self.stopwords = set()
        
        if stopwords_file and Path(stopwords_file).exists():
            self.load_stopwords()
        else:
            logger.warning(f"Stopwords file not found: {stopwords_file}")
            self.stopwords = self._get_default_stopwords()
    
    def load_stopwords(self):
        """Load stopwords from file."""
        try:
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                words = [line.strip().lower() for line in f if line.strip()]
                self.stopwords = set(words)
            
            logger.info(f"Loaded {len(self.stopwords)} stopwords from {self.stopwords_file}")
            print(f"✓ Đã tải {len(self.stopwords)} stopwords")
            
        except Exception as e:
            logger.error(f"Error loading stopwords: {e}")
            self.stopwords = self._get_default_stopwords()
    
    def _get_default_stopwords(self):
        """Get default stopwords if file not available."""
        logger.warning("Using default stopwords")
        return {
            'là', 'của', 'và', 'có', 'được', 'một', 'trong', 'với',
            'các', 'những', 'này', 'đó', 'cho', 'không', 'người',
            'từ', 'đã', 'sẽ', 'theo', 'về', 'hay', 'hoặc', 'để',
        }
    
    def get_stopwords(self):
        """Get stopwords set."""
        return self.stopwords
    
    def add_stopwords(self, words):
        """
        Add custom stopwords.
        
        Args:
            words: List or set of words to add
        """
        if isinstance(words, str):
            words = [words]
        
        self.stopwords.update(w.lower() for w in words)
        logger.debug(f"Added {len(words)} custom stopwords")
    
    def remove_stopwords(self, words):
        """
        Remove stopwords.
        
        Args:
            words: List or set of words to remove
        """
        if isinstance(words, str):
            words = [words]
        
        for word in words:
            self.stopwords.discard(word.lower())
        
        logger.debug(f"Removed {len(words)} stopwords")
    
    def is_stopword(self, word):
        """Check if a word is stopword."""
        return word.lower() in self.stopwords