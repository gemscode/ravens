# helpers/file_io.py
import os
import zlib
import logging
from typing import Optional
from models import ResumeMetadata

logger = logging.getLogger(__name__)

def save_uploaded_file(file, user_id: str, upload_dir: str) -> str:
    """Save uploaded file with proper permissions and return path"""
    try:
        os.makedirs(upload_dir, exist_ok=True, mode=0o755)
        file_path = os.path.join(upload_dir, file.name)
        
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
            
        return file_path
    except Exception as e:
        logger.error(f"File save failed: {str(e)}")
        raise

def calculate_checksum(file_path: str) -> Optional[str]:
    """Calculate CRC32 checksum for file content"""
    buf_size = 65536  # 64KB chunks
    crc = 0
    try:
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                crc = zlib.crc32(data, crc)
        return format(crc & 0xFFFFFFFF, '08x')
    except Exception as e:
        logger.error(f"Checksum calculation failed: {str(e)}")
        return None

