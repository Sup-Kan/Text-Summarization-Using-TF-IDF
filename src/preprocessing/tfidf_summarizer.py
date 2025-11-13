"""
TF-IDF based extractive summarization using VnCoreNLP
"""

import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from vncorenlp import VnCoreNLP

logger = logging.getLogger(__name__)


class TfidfSummarizer:
    """TF-IDF based extractive text summarizer with VnCoreNLP."""
    
    def __init__(self, vncorenlp_dir, stopwords=None, num_sentences=3, 
                 use_idf=True, smooth_idf=True):
        """
        Initialize summarizer.
        
        Args:
            vncorenlp_dir: Path to VnCoreNLP directory
            stopwords: Set or list of stopwords
            num_sentences: Number of sentences in summary
            use_idf: Use IDF weighting
            smooth_idf: Apply IDF smoothing
        """
        self.vncorenlp_dir = vncorenlp_dir
        self.stopwords = stopwords or set()
        self.num_sentences = num_sentences
        self.use_idf = use_idf
        self.smooth_idf = smooth_idf
        self.annotator = None
        
        logger.info(f"TfidfSummarizer initialized: num_sentences={num_sentences}, "
                   f"stopwords={len(self.stopwords)}")
    
    def _init_annotator(self):
        """Initialize VnCoreNLP annotator (lazy loading)."""
        if self.annotator is None:
            try:
                logger.info("Initializing VnCoreNLP annotator for word segmentation...")
                self.annotator = VnCoreNLP(
                    address=f"{VNCORENLP_HOST}:{VNCORENLP_PORT}",
                    annotators="wseg",
                    max_heap_size=VNCORENLP_MAX_HEAP_SIZE
                )
                logger.info("VnCoreNLP annotator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VnCoreNLP: {e}")
                raise
    
    def _tokenize_vietnamese(self, text):
        """
        Tokenize Vietnamese text using VnCoreNLP.
        
        Args:
            text: Input text
        
        Returns:
            list: List of tokens
        """
        try:
            self._init_annotator()
            
            # Word segmentation
            segmented = self.annotator.tokenize(text)
            
            # Flatten and filter
            tokens = []
            for sent in segmented:
                for word_list in sent:
                    for word in word_list:
                        # Convert to lowercase
                        word_lower = word.lower()
                        
                        # Filter: alphanumeric and not stopword
                        if word_lower.replace('_', '').isalnum() and word_lower not in self.stopwords:
                            tokens.append(word_lower)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error tokenizing: {e}")
            # Fallback
            return self._fallback_tokenize(text)
    
    def _fallback_tokenize(self, text):
        """Fallback tokenization (simple whitespace)."""
        tokens = text.lower().split()
        tokens = [t for t in tokens if t.isalnum() and t not in self.stopwords]
        logger.warning(f"Using fallback tokenization: {len(tokens)} tokens")
        return tokens
    
    def summarize(self, sentences):
        """
        Generate extractive summary using TF-IDF.
        
        Args:
            sentences: List of sentences
        
        Returns:
            dict: {
                'summary': List of selected sentences,
                'indices': Indices of selected sentences,
                'scores': TF-IDF scores for all sentences
            }
        """
        if not sentences:
            logger.warning("No sentences to summarize")
            return {'summary': [], 'indices': [], 'scores': []}
        
        # Adjust number of sentences
        num_sentences = min(self.num_sentences, len(sentences))
        
        if len(sentences) <= num_sentences:
            logger.info(f"Document has {len(sentences)} sentences, returning all")
            return {
                'summary': sentences,
                'indices': list(range(len(sentences))),
                'scores': [1.0] * len(sentences)
            }
        
        try:
            # === STEP 1: Compute TF-IDF ===
            logger.debug("Computing TF-IDF matrix with VnCoreNLP")
            vectorizer = TfidfVectorizer(
                tokenizer=self._tokenize_vietnamese,
                use_idf=self.use_idf,
                smooth_idf=self.smooth_idf,
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            logger.debug(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
            
            # === STEP 2: Score sentences ===
            sentence_scores = np.sum(tfidf_matrix.toarray(), axis=1)
            logger.debug(f"Sentence scores range: [{sentence_scores.min():.4f}, {sentence_scores.max():.4f}]")
            
            # === STEP 3: Select top sentences ===
            top_indices = np.argsort(sentence_scores)[-num_sentences:]
            logger.debug(f"Top sentence indices: {top_indices}")
            
            # === STEP 4: Re-order by original position ===
            ordered_indices = sorted(top_indices)
            logger.info(f"Selected sentences at indices: {ordered_indices}")
            
            # === STEP 5: Generate summary ===
            summary_sentences = [sentences[i] for i in ordered_indices]
            
            return {
                'summary': summary_sentences,
                'indices': ordered_indices,
                'scores': sentence_scores.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}", exc_info=True)
            return {'summary': [], 'indices': [], 'scores': []}
    
    def summarize_text(self, text):
        """
        Summarize text directly (convenience method).
        
        Args:
            text: Input text
        
        Returns:
            str: Summary text
        """
        from .sentence_tokenizer import SentenceTokenizer
        
        tokenizer = SentenceTokenizer(self.vncorenlp_dir)
        sentences = tokenizer.tokenize(text)
        
        result = self.summarize(sentences)
        return ' '.join(result['summary'])
    
    def close(self):
        """Close VnCoreNLP annotator."""
        if self.annotator:
            self.annotator.close()
            logger.info("VnCoreNLP annotator closed")