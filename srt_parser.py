import re
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry with timing and text."""
    index: int
    start_time: str
    end_time: str
    text: str
    
    def get_start_seconds(self) -> float:
        """Convert start time to seconds for easier processing."""
        return self._time_to_seconds(self.start_time)
    
    def get_end_seconds(self) -> float:
        """Convert end time to seconds for easier processing."""
        return self._time_to_seconds(self.end_time)
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert SRT time format (HH:MM:SS,mmm) to seconds."""
        # Replace comma with dot for milliseconds
        time_str = time_str.replace(',', '.')
        
        # Parse the time
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_and_ms = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds_and_ms

class SRTParser:
    """Parser for SRT subtitle files."""
    
    def parse_srt_file(self, srt_path: str) -> List[SubtitleEntry]:
        """
        Parse an SRT file and return a list of subtitle entries.
        
        Args:
            srt_path: Path to the SRT file
            
        Returns:
            List of SubtitleEntry objects
        """
        if not os.path.exists(srt_path):
            raise FileNotFoundError(f"SRT file not found: {srt_path}")
        
        with open(srt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return self._parse_srt_content(content)
    
    def _parse_srt_content(self, content: str) -> List[SubtitleEntry]:
        """Parse SRT content and extract subtitle entries."""
        entries = []
        
        # Split content into blocks (separated by double newlines)
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            if not block.strip():
                continue
                
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # First line is the index
                index = int(lines[0].strip())
                
                # Second line is the timing
                timing_line = lines[1].strip()
                timing_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timing_line)
                
                if not timing_match:
                    continue
                
                start_time = timing_match.group(1)
                end_time = timing_match.group(2)
                
                # Remaining lines are the subtitle text
                text = '\n'.join(lines[2:]).strip()
                
                entry = SubtitleEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                )
                
                entries.append(entry)
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Skipping malformed subtitle block: {e}")
                continue
        
        return entries
    
    def get_subtitle_keywords(self, entry: SubtitleEntry) -> List[str]:
        """
        Extract keywords from subtitle text for image matching.
        
        Args:
            entry: SubtitleEntry object
            
        Returns:
            List of keywords extracted from the subtitle text
        """
        # Remove HTML tags and special characters
        text = re.sub(r'<[^>]+>', '', entry.text)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words and filter out common words
        words = text.lower().split()
        
        # Basic stopwords to filter out
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their'
        }
        
        # Filter out stopwords and short words
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        
        return keywords
