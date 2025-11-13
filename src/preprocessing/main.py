"""
Main entry point for text preprocessing with VnCoreNLP
"""

import sys
import logging
from pathlib import Path

from src.preprocessing.config import VNCORENLP_DOWNLOAD_URL
from src.preprocessing.config import LOG_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOG_DIR
from src.preprocessing.config import VNCORENLP_DIR, VNCORENLP_JAR, VNCORENLP_PORT
from src.preprocessing.config import SUMMARY_SENTENCE_COUNT, STOPWORDS_FILE
from src.preprocessing.vncorenlp_setup import setup_vncorenlp
from src.preprocessing.processor import TextProcessor


def setup_logging(log_dir):
    """Setup logging for preprocessing."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / 'processing.log'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("TEXT PREPROCESSING WITH VNCORENLP STARTED")
    logger.info("="*80)
    
    return logger


def main(raw_data_dir=None, processed_data_dir=None, num_sentences=None):
    """
    Main preprocessing pipeline with VnCoreNLP.
    
    Args:
        raw_data_dir: Override default raw data directory
        processed_data_dir: Override default processed data directory
        num_sentences: Number of sentences in summary
    """
    # Setup logging
    logger = setup_logging(LOG_DIR)
    
    raw_dir = raw_data_dir or RAW_DATA_DIR
    proc_dir = processed_data_dir or PROCESSED_DATA_DIR
    num_sent = num_sentences or SUMMARY_SENTENCE_COUNT
    
    logger.info(f"Configuration:")
    logger.info(f"  Raw data: {raw_dir}")
    logger.info(f"  Processed data: {proc_dir}")
    logger.info(f"  Summary sentences: {num_sent}")
    logger.info(f"  VnCoreNLP dir: {VNCORENLP_DIR}")
    
    # ==========================================
    # STEP 1: Setup VnCoreNLP
    # ==========================================
    print("\n" + "="*80)
    print("BƯỚC 1: KIỂM TRA VÀ CÀI ĐẶT VNCORENLP")
    print("="*80)
    
    try:
        success = setup_vncorenlp(VNCORENLP_DIR, VNCORENLP_DOWNLOAD_URL)
        if not success:
            logger.error("VnCoreNLP setup failed")
            print("✗ Cài đặt VnCoreNLP thất bại")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error setting up VnCoreNLP: {e}", exc_info=True)
        print(f"✗ Lỗi: {e}")
        sys.exit(1)
    
    # ==========================================
    # STEP 2: Check raw data
    # ==========================================
    print("\n" + "="*80)
    print("BƯỚC 2: KIỂM TRA DỮ LIỆU NGUỒN")
    print("="*80)
    
    if not Path(raw_dir).exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        print(f"✗ Lỗi: Không tìm thấy thư mục dữ liệu thô: {raw_dir}")
        sys.exit(1)
    
    print(f"✓ Tìm thấy thư mục dữ liệu: {raw_dir}")
    
    # ==========================================
    # STEP 3: Start VnCoreNLP server
    # ==========================================
    print("\n" + "="*80)
    print("BƯỚC 3: KHỞI ĐỘNG VNCORENLP SERVER")
    print("="*80)
    print(f"⚠  Lưu ý: Bạn cần chạy VnCoreNLP server riêng biệt:")
    print(f"   java -Xmx2g -jar {VNCORENLP_DIR}/{VNCORENLP_JAR} -p {VNCORENLP_PORT} -annotators wseg")
    print()
    
    input("Nhấn ENTER sau khi đã khởi động server...")
    
    # ==========================================
    # STEP 4: Process data
    # ==========================================
    print("\n" + "="*80)
    print("BƯỚC 4: XỬ LÝ DỮ LIỆU")
    print("="*80)
    
    try:
        # Initialize processor
        processor = TextProcessor(
            raw_data_dir=raw_dir,
            processed_data_dir=proc_dir,
            vncorenlp_dir=VNCORENLP_DIR,
            stopwords_file=STOPWORDS_FILE,
            num_sentences=num_sent
        )
        
        # Process all data
        stats = processor.process_all()
        
        # Cleanup
        processor.cleanup()
        
        # ==========================================
        # STEP 5: Results
        # ==========================================
        print("\n" + "="*80)
        print("HOÀN THÀNH XỬ LÝ!")
        print("="*80)
        print(f"✅ Đã xử lý {stats['categories']} chuyên mục chính")
        print(f"✅ Đã xử lý {stats['subcategories']} chuyên mục con")
        print(f"✅ Đã tạo tóm tắt cho {stats['processed']} bài báo")
        if stats['failed'] > 0:
            print(f"⚠  {stats['failed']} bài báo thất bại")
        print(f"✅ Dữ liệu được lưu trong: {proc_dir}")
        print(f"✅ Log được lưu trong: {LOG_DIR}")
        print("="*80)
        
        logger.info("Preprocessing completed successfully")
        
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        print(f"\n✗ LỖI NGHIÊM TRỌNG: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()