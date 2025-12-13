"""
Audio Extractor Service
Handles YouTube audio extraction using yt-dlp
"""
import yt_dlp
import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProgressCallback:
    """
    Progress callback for yt-dlp downloads
    Updates job progress in database
    """
    
    def __init__(self, job_id: str):
        """
        Initialize progress callback
        
        Args:
            job_id: Job identifier to update
        """
        self.job_id = job_id
        self.job_manager = None
        
        # Lazy import to avoid circular dependency
        try:
            from services.job_manager import JobManager
            self.job_manager = JobManager()
        except ImportError:
            logger.warning("JobManager not available for progress updates")
    
    def hook(self, d: Dict[str, Any]):
        """
        Progress hook called by yt-dlp
        
        Args:
            d: Progress dictionary from yt-dlp
        """
        if not self.job_manager:
            return
        
        status = d.get('status')
        
        if status == 'downloading':
            # Calculate download progress
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                progress = int((downloaded / total) * 100)
                # Limit progress to 0-90% during download (reserve 90-100% for processing)
                progress = min(progress * 0.9, 90)
                self.job_manager.update_job_progress(self.job_id, int(progress))
                
        elif status == 'finished':
            # Download finished, processing audio
            self.job_manager.update_job_progress(self.job_id, 95, "Processing audio")
            logger.info(f"Download finished for job {self.job_id}")
        
        elif status == 'error':
            logger.error(f"Download error for job {self.job_id}")


@dataclass
class AudioExtractionResult:
    """Result of audio extraction operation"""
    success: bool
    file_path: Optional[str]
    duration_seconds: Optional[int]
    title: Optional[str]
    error: Optional[str]


class AudioExtractor:
    """
    Service for extracting audio from YouTube videos
    """
    
    # Maximum video duration in seconds (60 minutes)
    MAX_DURATION_SECONDS = 3600
    
    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
    ]
    
    def __init__(self, output_dir: str = "audio_files"):
        """
        Initialize AudioExtractor
        
        Args:
            output_dir: Directory to store extracted audio files
        """
        self.output_dir = output_dir
        self.audio_dir = output_dir
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def validate_youtube_url(self, url: str) -> bool:
        """
        Validate if URL is a valid YouTube URL
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid YouTube URL, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        for pattern in self.YOUTUBE_PATTERNS:
            if re.match(pattern, url):
                return True
        
        return False
    
    def get_video_info(self, youtube_url: str) -> Optional[Dict[str, Any]]:
        """
        Get video information without downloading
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dict with video info or None if error
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
    
    def extract_audio(self, youtube_url: str, job_id: str) -> AudioExtractionResult:
        """
        Extract audio from YouTube video
        
        Args:
            youtube_url: YouTube video URL
            job_id: Unique job identifier
            
        Returns:
            AudioExtractionResult: Result of extraction operation
        """
        # Validate URL
        if not self.validate_youtube_url(youtube_url):
            return AudioExtractionResult(
                success=False,
                file_path=None,
                duration_seconds=None,
                title=None,
                error="Invalid YouTube URL format"
            )
        
        # Define output file path
        output_path = os.path.join(self.output_dir, f"{job_id}.%(ext)s")
        
        # Create progress callback
        progress_callback = ProgressCallback(job_id)
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'extract_audio': True,
            'progress_hooks': [progress_callback.hook],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                logger.info(f"Extracting info for {youtube_url}")
                info = ydl.extract_info(youtube_url, download=False)
                
                if not info:
                    return AudioExtractionResult(
                        success=False,
                        file_path=None,
                        duration_seconds=None,
                        title=None,
                        error="Could not retrieve video information"
                    )
                
                # Check duration
                duration = info.get('duration', 0)
                if duration > self.MAX_DURATION_SECONDS:
                    return AudioExtractionResult(
                        success=False,
                        file_path=None,
                        duration_seconds=duration,
                        title=info.get('title'),
                        error=f"Video duration exceeds 60 minute limit ({duration}s)"
                    )
                
                # Download audio
                logger.info(f"Downloading audio for {youtube_url}")
                ydl.extract_info(youtube_url, download=True)
                
                # Construct final file path
                final_path = os.path.join(self.output_dir, f"{job_id}.m4a")
                
                return AudioExtractionResult(
                    success=True,
                    file_path=final_path,
                    duration_seconds=duration,
                    title=info.get('title'),
                    error=None
                )
                
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download error for {youtube_url}: {error_msg}")
            
            # Check for specific error types
            if "Video unavailable" in error_msg:
                error_msg = "Video is unavailable or private"
            elif "copyright" in error_msg.lower():
                error_msg = "Video has copyright restrictions"
            
            return AudioExtractionResult(
                success=False,
                file_path=None,
                duration_seconds=None,
                title=None,
                error=error_msg
            )
            
        except Exception as e:
            logger.error(f"Unexpected error extracting audio: {e}")
            return AudioExtractionResult(
                success=False,
                file_path=None,
                duration_seconds=None,
                title=None,
                error=f"Extraction failed: {str(e)}"
            )
