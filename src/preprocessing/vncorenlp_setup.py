import os
import sys
import logging
import zipfile
import shutil
import subprocess
from pathlib import Path
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class VnCoreNLPSetup:
    """Setup VnCoreNLP automatically."""
    
    def __init__(self, install_dir, download_url):
        """
        Initialize setup.
        
        Args:
            install_dir: Directory to install VnCoreNLP
            download_url: URL to download VnCoreNLP
        """
        self.install_dir = Path(install_dir)
        self.download_url = download_url
        self.jar_path = self.install_dir / 'VnCoreNLP-1.2.jar'
        self.models_dir = self.install_dir / 'models'
        
    def is_installed(self):
        """Check if VnCoreNLP is already installed."""
        return self.jar_path.exists() and self.models_dir.exists()
    
    def download_file(self, url, destination):
        """
        Download file with progress bar.
        
        Args:
            url: URL to download
            destination: Path to save file
        """
        logger.info(f"Downloading from {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destination, 'wb') as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Downloaded to {destination}")
    
    def extract_zip(self, zip_path, extract_to):
        """
        Extract ZIP file.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Directory to extract to
        """
        logger.info(f"Extracting {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        logger.info(f"Extracted to {extract_to}")
    
    def setup(self):
        """
        Download and setup VnCoreNLP.
        
        Returns:
            bool: Success status
        """
        if self.is_installed():
            logger.info("VnCoreNLP already installed")
            print("✓ VnCoreNLP đã được cài đặt")
            return True
        
        try:
            # Create install directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Download
            print("📥 Đang tải VnCoreNLP v1.2...")
            zip_path = self.install_dir / 'VnCoreNLP-1.2.zip'
            self.download_file(self.download_url, zip_path)
            
            # Extract
            print("📦 Đang giải nén...")
            temp_extract = self.install_dir / 'temp_extract'
            self.extract_zip(zip_path, temp_extract)
            
            # Move files to correct location
            print("📁 Đang cài đặt...")
            extracted_dir = temp_extract / 'VnCoreNLP-1.2'
            
            if not extracted_dir.exists():
                # Try alternative structure
                extracted_dir = list(temp_extract.glob('VnCoreNLP*'))[0]
            
            # Move JAR file
            jar_source = extracted_dir / 'VnCoreNLP-1.2.jar'
            if jar_source.exists():
                shutil.move(str(jar_source), str(self.jar_path))
                logger.info(f"Moved JAR to {self.jar_path}")
            
            # Move models directory
            models_source = extracted_dir / 'models'
            if models_source.exists():
                if self.models_dir.exists():
                    shutil.rmtree(self.models_dir)
                shutil.move(str(models_source), str(self.models_dir))
                logger.info(f"Moved models to {self.models_dir}")
            
            # Create stopwords directory and file
            self.setup_stopwords()
            
            # Cleanup
            zip_path.unlink()
            shutil.rmtree(temp_extract)
            
            print("✓ Cài đặt VnCoreNLP thành công!")
            logger.info("VnCoreNLP setup completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up VnCoreNLP: {e}", exc_info=True)
            print(f"✗ Lỗi cài đặt VnCoreNLP: {e}")
            return False
    
    def setup_stopwords(self):
        """Create default Vietnamese stopwords file."""
        stopwords_dir = self.install_dir / 'stopwords'
        stopwords_dir.mkdir(exist_ok=True)
        
        stopwords_file = stopwords_dir / 'vietnamese-stopwords.txt'
        
        # Default Vietnamese stopwords
        default_stopwords = [
            # Articles
            'các', 'một', 'những', 'cái', 'chiếc', 'con', 'người',
            
            # Conjunctions
            'và', 'hay', 'hoặc', 'nhưng', 'mà', 'vì', 'nên', 'thì', 'nếu',
            
            # Prepositions
            'của', 'cho', 'với', 'về', 'từ', 'trong', 'ngoài', 'trên', 'dưới',
            'đến', 'tại', 'bởi', 'theo', 'qua', 'sau', 'trước', 'giữa',
            
            # Pronouns
            'tôi', 'bạn', 'anh', 'chị', 'em', 'chúng', 'nó', 'họ', 'chúng_ta',
            'ta', 'mình', 'ai', 'gì', 'đâu', 'sao', 'nào', 'kia', 'này', 'đó',
            
            # Verbs
            'là', 'được', 'có', 'không', 'đã', 'sẽ', 'đang', 'bị', 'phải',
            'cần', 'muốn', 'thể', 'nên', 'nữa', 'đang', 'vẫn', 'còn',
            
            # Adjectives/Adverbs
            'rất', 'lại', 'cũng', 'đều', 'như', 'thế', 'vậy', 'thật', 'quá',
            
            # Others
            'ra', 'vào', 'lên', 'xuống', 'đi', 'lại', 'về', 'đây', 'đấy',
            'ở', 'tới', 'nhiều', 'ít', 'hơn', 'nhất', 'cùng', 'mỗi',
        ]
        
        with open(stopwords_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(default_stopwords))
        
        logger.info(f"Created stopwords file: {stopwords_file}")
        print(f"✓ Đã tạo file stopwords: {stopwords_file}")
    
    def check_java(self):
        """Check if Java is installed."""
        try:
            result = subprocess.run(
                ['java', '-version'],
                capture_output=True,
                text=True
            )
            logger.info("Java is installed")
            return True
        except FileNotFoundError:
            logger.error("Java not found")
            print("✗ Lỗi: Không tìm thấy Java. Vui lòng cài đặt Java JDK 8+")
            return False


def setup_vncorenlp(install_dir, download_url):
    """
    Convenience function to setup VnCoreNLP.
    
    Args:
        install_dir: Directory to install
        download_url: Download URL
    
    Returns:
        bool: Success status
    """
    setup = VnCoreNLPSetup(install_dir, download_url)
    
    # Check Java
    if not setup.check_java():
        return False
    
    # Setup VnCoreNLP
    return setup.setup()