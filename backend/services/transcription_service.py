"""
Transcription Service
Handles audio-to-text conversion using OpenAI Whisper API
"""
from openai import OpenAI
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """
    Result of transcription operation
    """
    success: bool
    text: Optional[str] = None
    language_detected: Optional[str] = None
    model: Optional[str] = None
    duration_seconds: Optional[int] = None
    error: Optional[str] = None


class TranscriptionService:
    """
    Service for transcribing audio files using OpenAI Whisper API
    """
    
    # File size limit (25MB)
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize transcription service
        
        Args:
            api_key: OpenAI API key (uses env var if not provided)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
        
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            language: Target language code (ja, en, etc)
            model: Whisper model to use
            prompt: Optional prompt hint for better accuracy
            
        Returns:
            Dict with transcription result
        """
        # Check if file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return {
                'success': False,
                'error': f"Audio file not found: {audio_file_path}"
            }
        
        # Check file size
        file_size = os.path.getsize(audio_file_path)
        if file_size > self.MAX_FILE_SIZE_BYTES:
            logger.error(f"File size {file_size} exceeds 25MB limit")
            return {
                'success': False,
                'error': f"File size exceeds 25MB limit (current: {file_size / 1024 / 1024:.1f}MB)"
            }
        
        if not self.client:
            logger.error("OpenAI client not initialized")
            return {
                'success': False,
                'error': "OpenAI API key not configured"
            }
        
        try:
            # Open audio file
            with open(audio_file_path, 'rb') as audio_file:
                # Prepare API parameters
                api_params = {
                    'model': model,
                    'file': audio_file,
                }
                
                # Add optional parameters
                if language:
                    api_params['language'] = language
                
                if prompt:
                    api_params['prompt'] = prompt
                
                # Call Whisper API
                logger.info(f"Transcribing {audio_file_path} with model {model}")
                response = self.client.audio.transcriptions.create(**api_params)
                
                # Extract result
                result = {
                    'success': True,
                    'text': response.text,
                    'model': model,
                }
                
                # Add detected language if available
                if hasattr(response, 'language'):
                    result['language_detected'] = response.language
                
                logger.info(f"Transcription completed: {len(response.text)} characters")
                return result
                
        except FileNotFoundError as e:
            logger.error(f"File not found during transcription: {e}")
            return {
                'success': False,
                'error': f"File not found: {str(e)}"
            }
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                'success': False,
                'error': f"Transcription failed: {str(e)}"
            }

    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """Wrapper that returns a typed TranscriptionResult"""
        raw = self.transcribe(
            audio_file_path=audio_path,
            language=language,
            model=model,
            prompt=prompt,
        )

        return TranscriptionResult(
            success=raw.get('success', False),
            text=raw.get('text'),
            language_detected=raw.get('language_detected'),
            model=raw.get('model', model),
            error=raw.get('error'),
        )
