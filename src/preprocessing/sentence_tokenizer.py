"""
Sentence tokenization using VnCoreNLP
"""

import logging
from vncorenlp import VnCoreNLP

logger = logging.getLogger(__name__)


class SentenceTokenizer:
    """Vietnamese sentence tokenizer using VnCoreNLP."""
    
    def __init__(self, vncorenlp_dir, min_length=10, max_length=500):
        """
        Initialize tokenizer.
        
        Args:
            vncorenlp_dir: Path to VnCoreNLP directory
            min_length: Minimum sentence length (characters)
            max_length: Maximum sentence length (characters)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.annotator = None
        self.vncorenlp_dir = vncorenlp_dir
        
        logger.info(f"SentenceTokenizer initialized: min={min_length}, max={max_length}")
    
    def _init_annotator(self):
        """Initialize VnCoreNLP annotator (lazy loading)."""
        if self.annotator is None:
            try:
                logger.info("Initializing VnCoreNLP annotator...")
                self.annotator = VnCoreNLP(
                    address=f"{VNCORENLP_HOST}:{VNCORENLP_PORT}",
                    annotators="wseg",
                    max_heap_size=VNCORENLP_MAX_HEAP_SIZE
                )
                logger.info("VnCoreNLP annotator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VnCoreNLP: {e}")
                raise
    
    def tokenize(self, text):
        """
        Tokenize text into sentences.
        
        Args:
            text: Input text
        
        Returns:
            list: List of sentences
        """
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return []
        
        try:
            self._init_annotator()
            
            # VnCoreNLP sentence segmentation
            # Output: list of sentences (each sentence is a list of word lists)
            annotated = self.annotator.tokenize(text)
            
            # Convert to sentence strings
            sentences = []
            for sent_words in annotated:
                # Join word lists in each sentence
                sent_text = ' '.join([' '.join(word_list) for word_list in sent_words])
                sentences.append(sent_text)
            
            logger.debug(f"Tokenized {len(sentences)} sentences")
            
            # Filter by length
            filtered = []
            for sent in sentences:
                sent_clean = sent.strip()
                length = len(sent_clean)
                
                if self.min_length <= length <= self.max_length:
                    filtered.append(sent_clean)
                else:
                    logger.debug(f"Filtered sentence (length={length}): {sent_clean[:50]}...")
            
            logger.info(f"Kept {len(filtered)}/{len(sentences)} sentences after filtering")
            return filtered
            
        except Exception as e:
            logger.error(f"Error tokenizing text: {e}", exc_info=True)
            # Fallback to simple split
            logger.warning("Using fallback sentence splitting")
            return self._fallback_tokenize(text)
    
    def _fallback_tokenize(self, text):
        """Fallback sentence tokenization using simple rules."""
        import re
        
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Filter by length
        filtered = [s for s in sentences if self.min_length <= len(s) <= self.max_length]
        
        logger.warning(f"Fallback tokenization: {len(filtered)} sentences")
        return filtered
    
    def tokenize_batch(self, texts):
        """
        Tokenize multiple texts.
        
        Args:
            texts: List of texts
        
        Returns:
            list: List of sentence lists
        """
        return [self.tokenize(text) for text in texts]
    
    def close(self):
        """Close VnCoreNLP annotator."""
        if self.annotator:
            self.annotator.close()
            logger.info("VnCoreNLP annotator closed")