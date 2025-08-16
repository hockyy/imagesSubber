"""
Web session manager for the SRT Image Timeline Generator web app.
Manages user sessions and timeline data.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any

from srt_parser import SRTParser
from text_splitter import SmartTextSplitter
from brave_image_client import BraveImageClient


class TimelineSession:
    """Manages a user session for timeline generation."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.srt_file_path = None
        self.video_title = ""
        self.brave_api_key = ""
        self.text_splits = []
        self.selected_images = {}  # {split_index: [image_info_list]}
        self.search_results = {}   # {split_index: [image_results]}
        
        # Components
        self.srt_parser = SRTParser()
        self.text_splitter = SmartTextSplitter()
        self.brave_client = None
        
        self.created_at = datetime.now()
        
    def setup_brave_client(self, api_key: str) -> None:
        """Setup Brave API client."""
        self.brave_api_key = api_key
        self.brave_client = BraveImageClient(api_key)
        
    def process_srt_file(self, file_path: str, video_title: str) -> Tuple[int, int]:
        """
        Process SRT file and create text splits.
        
        Args:
            file_path: Path to the SRT file
            video_title: Title of the video
            
        Returns:
            Tuple of (segments_count, splits_count)
        """
        self.srt_file_path = file_path
        self.video_title = video_title
        
        # Parse SRT file
        subtitle_entries = self.srt_parser.parse_srt_file(file_path)
        if not subtitle_entries:
            raise ValueError("No subtitle entries found in SRT file")
        
        # Create text splits
        self.text_splits = []
        for i, entry in enumerate(subtitle_entries):
            splits = self.text_splitter.split_subtitle_text(
                entry.text, entry.start_time, entry.end_time, i
            )
            self.text_splits.extend(splits)
        
        return len(subtitle_entries), len(self.text_splits)


class WebSessionManager:
    """Manages web sessions for the application."""
    
    def __init__(self):
        self.sessions: Dict[str, TimelineSession] = {}
    
    def create_session(self) -> TimelineSession:
        """Create a new timeline session."""
        session_id = str(uuid.uuid4())
        session = TimelineSession(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> TimelineSession:
        """Get a session by ID."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id]
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self.sessions
    
    def remove_session(self, session_id: str) -> None:
        """Remove a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions older than max_age_hours.
        
        Returns:
            Number of sessions removed
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.created_at < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
        
        return len(old_sessions)
