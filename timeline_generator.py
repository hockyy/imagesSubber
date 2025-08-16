"""
Clean timeline generator using Brave Search API and smart text splitting.
"""

from typing import List, Dict, Any
from pathlib import Path

from srt_parser import SRTParser
from text_splitter import SmartTextSplitter
from brave_image_client import BraveImageClient
from image_downloader import ImageDownloader
from search_query_generator import SearchQueryGenerator
from statistics_tracker import StatisticsTracker
from timeline_operations import TimelineOperations

class TimelineGenerator:
    """Generates image timelines from SRT files using smart text splitting."""
    
    def __init__(self, brave_api_key: str, output_dir: str = "images"):
        """
        Initialize the timeline generator.
        
        Args:
            brave_api_key: Brave Search API key
            output_dir: Directory to save downloaded images
        """
        self.srt_parser = SRTParser()
        self.text_splitter = SmartTextSplitter()
        self.brave_client = BraveImageClient(brave_api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.stats_tracker = StatisticsTracker()
        self.image_downloader = ImageDownloader(self.brave_client, self.output_dir, self.stats_tracker)
        self.query_generator = SearchQueryGenerator()
        self.timeline_ops = TimelineOperations(self.text_splitter, self.stats_tracker)
    
    def generate_timeline(self, srt_path: str, video_title: str, 
                         images_per_split: int = 2) -> List[Dict[str, Any]]:
        """
        Generate timeline from SRT file with smart text splitting.
        
        Args:
            srt_path: Path to SRT file
            video_title: Video title for organizing images
            images_per_split: Number of images to download per text split
            
        Returns:
            Timeline data as list of segments
        """
        print(f"🎬 Generating timeline for: {video_title}")
        print(f"📁 Images will be saved to: {self.output_dir / video_title}")
        
        # Parse SRT file
        subtitle_entries = self.srt_parser.parse_srt_file(srt_path)
        if not subtitle_entries:
            raise ValueError("No subtitle entries found in SRT file")
        
        print(f"📝 Found {len(subtitle_entries)} subtitle segments")
        
        # Create video directory
        video_dir = self.output_dir / video_title
        video_dir.mkdir(exist_ok=True)
        
        timeline = []
        all_splits = []
        
        # Process each subtitle segment
        for i, entry in enumerate(subtitle_entries):
            print(f"\nProcessing segment {i + 1}/{len(subtitle_entries)}: '{entry.text[:50]}...'")
            
            # Split the subtitle text
            splits = self.text_splitter.split_subtitle_text(
                entry.text, entry.start_time, entry.end_time, i
            )
            all_splits.extend(splits)
            
            # Process each split
            for split in splits:
                print(f"  Split {split.split_index}: '{split.text[:30]}...' ({len(split.keywords)} keywords)")
                
                # Generate search queries and download images for this split
                search_queries = self.query_generator.generate_search_queries(split.keywords)
                images = self.image_downloader.download_images_for_split(
                    split, video_title, images_per_split, search_queries
                )
                
                # Create timeline entry
                timeline_entry = {
                    "start": split.start_time,
                    "end": split.end_time,
                    "image": images
                }
                
                timeline.append(timeline_entry)
        
        # Update statistics
        self.stats_tracker.set_segments_count(len(subtitle_entries))
        self.stats_tracker.set_splits_count(len(all_splits))
        
        print(f"\n✅ Generated {len(timeline)} timeline entries from {len(all_splits)} text splits")
        return timeline
    

    
    def save_timeline(self, timeline: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save timeline to JSON file.
        
        Args:
            timeline: Timeline data
            output_path: Output file path
        """
        self.timeline_ops.save_timeline(timeline, output_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return self.stats_tracker.get_statistics()
    
    def preview_timeline(self, timeline: List[Dict[str, Any]], max_items: int = 10) -> None:
        """
        Print timeline preview.
        
        Args:
            timeline: Timeline data
            max_items: Maximum items to show
        """
        self.timeline_ops.preview_timeline(timeline, max_items)
