"""
Smart text splitter for subtitle segments.
Splits subtitle text based on duration and word count.
"""

import re
import math
from typing import List, Tuple
from dataclasses import dataclass

try:
    import nltk
    from nltk.corpus import stopwords
    # Download stopwords if not already present
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("Warning: NLTK not available, using basic stopwords")

@dataclass
class TextSplit:
    """Represents a split portion of subtitle text."""
    text: str
    start_time: str
    end_time: str
    keywords: List[str]
    original_segment_index: int
    split_index: int

class SmartTextSplitter:
    """Splits subtitle text intelligently based on duration and content."""
    
    def __init__(self):
        """Initialize the text splitter."""
        if NLTK_AVAILABLE:
            # Use NLTK stopwords (more comprehensive)
            self.stopwords = set(stopwords.words('english'))
        else:
            # Fallback to basic stopwords
            self.stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
                'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
                'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
                'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
                'its', 'our', 'their'
            }
    
    def split_subtitle_text(self, text: str, start_time: str, end_time: str, 
                           segment_index: int) -> List[TextSplit]:
        """
        Split subtitle text into multiple parts based on duration and content.
        
        Args:
            text: Subtitle text to split
            start_time: Start time in SRT format
            end_time: End time in SRT format
            segment_index: Index of the original subtitle segment
            
        Returns:
            List of TextSplit objects
        """
        # Calculate duration in seconds
        start_seconds = self._time_to_seconds(start_time)
        end_seconds = self._time_to_seconds(end_time)
        duration = end_seconds - start_seconds
        
        # Calculate number of splits based on duration only:
        # divide by 3 seconds and ceil
        num_splits = math.ceil(duration / 3.0)
        
        print(f"  Duration: {duration:.1f}s, Splits: {num_splits}")
        
        if num_splits <= 1:
            # No splitting needed
            keywords = self._extract_keywords(text)
            return [TextSplit(
                text=text.strip(),
                start_time=start_time,
                end_time=end_time,
                keywords=keywords,
                original_segment_index=segment_index,
                split_index=0
            )]
        
        # Split the text into meaningful chunks
        text_chunks = self._split_text_into_chunks(text, num_splits)
        
        # Create time splits
        time_splits = []
        split_duration = duration / num_splits
        
        for i, chunk in enumerate(text_chunks):
            split_start = start_seconds + (i * split_duration)
            split_end = start_seconds + ((i + 1) * split_duration)
            
            # Ensure last split ends at original end time
            if i == len(text_chunks) - 1:
                split_end = end_seconds
            
            keywords = self._extract_keywords(chunk)
            
            time_splits.append(TextSplit(
                text=chunk.strip(),
                start_time=self._seconds_to_time(split_start),
                end_time=self._seconds_to_time(split_end),
                keywords=keywords,
                original_segment_index=segment_index,
                split_index=i
            ))
        
        return time_splits
    
    def _split_text_into_chunks(self, text: str, num_chunks: int) -> List[str]:
        """
        Split text into meaningful chunks.
        
        Args:
            text: Text to split
            num_chunks: Number of chunks to create
            
        Returns:
            List of text chunks
        """
        if num_chunks <= 1:
            return [text]
        
        # Clean and tokenize
        words = self._tokenize_text(text)
        
        if len(words) <= num_chunks:
            # Each word becomes a chunk
            return words
        
        # Try to split at natural boundaries (punctuation, conjunctions)
        sentences = self._split_into_sentences(text)
        
        if len(sentences) >= num_chunks:
            # Distribute sentences among chunks
            chunks = []
            sentences_per_chunk = len(sentences) // num_chunks
            remainder = len(sentences) % num_chunks
            
            start_idx = 0
            for i in range(num_chunks):
                chunk_size = sentences_per_chunk + (1 if i < remainder else 0)
                chunk_sentences = sentences[start_idx:start_idx + chunk_size]
                chunks.append(' '.join(chunk_sentences))
                start_idx += chunk_size
            
            return chunks
        
        # Fall back to word-based splitting
        words_per_chunk = len(words) // num_chunks
        remainder = len(words) % num_chunks
        
        chunks = []
        start_idx = 0
        
        for i in range(num_chunks):
            chunk_size = words_per_chunk + (1 if i < remainder else 0)
            chunk_words = words[start_idx:start_idx + chunk_size]
            chunks.append(' '.join(chunk_words))
            start_idx += chunk_size
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences or meaningful phrases."""
        # Split on punctuation and common conjunctions
        patterns = [
            r'[.!?]+\s+',  # Sentence endings
            r',\s+(?:and|or|but|so|yet|for|nor)\s+',  # Conjunctions with commas
            r'\s+(?:and|or|but|so|yet|for|nor)\s+',   # Conjunctions
            r',\s+',       # Simple commas
        ]
        
        sentences = [text]
        
        for pattern in patterns:
            new_sentences = []
            for sentence in sentences:
                parts = re.split(pattern, sentence)
                new_sentences.extend([part.strip() for part in parts if part.strip()])
            sentences = new_sentences
        
        return sentences
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Remove HTML tags and special characters, keep basic punctuation
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'[^\w\s.,!?-]', ' ', clean_text)
        
        # Split into words
        words = clean_text.split()
        return [word for word in words if len(word) > 0]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text, removing stopwords."""
        words = self._tokenize_text(text.lower())
        
        # Remove stopwords and short words
        keywords = []
        for word in words:
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 2 and clean_word not in self.stopwords:
                keywords.append(clean_word)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(keywords))
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert SRT time format to seconds."""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    def get_split_statistics(self, splits: List[TextSplit]) -> dict:
        """Get statistics about the splits."""
        if not splits:
            return {}
        
        total_duration = sum(
            self._time_to_seconds(split.end_time) - self._time_to_seconds(split.start_time)
            for split in splits
        )
        
        return {
            'total_splits': len(splits),
            'total_duration': round(total_duration, 2),
            'average_duration': round(total_duration / len(splits), 2),
            'total_keywords': sum(len(split.keywords) for split in splits),
            'average_keywords': round(sum(len(split.keywords) for split in splits) / len(splits), 2)
        }
