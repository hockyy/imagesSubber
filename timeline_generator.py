"""
Clean timeline generator using Brave Search API and smart text splitting.
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path

from srt_parser import SRTParser
from text_splitter import SmartTextSplitter, TextSplit
from brave_image_client import BraveImageClient

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
        
        # Statistics tracking
        self.stats = {
            'total_segments': 0,
            'total_splits': 0,
            'images_downloaded': 0,
            'images_failed': 0
        }
    
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
                
                # Search and download images for this split
                images = self._download_images_for_split(split, video_title, images_per_split)
                
                # Create timeline entry
                timeline_entry = {
                    "start": split.start_time,
                    "end": split.end_time,
                    "image": images
                }
                
                timeline.append(timeline_entry)
        
        # Update statistics
        self.stats['total_segments'] = len(subtitle_entries)
        self.stats['total_splits'] = len(all_splits)
        
        print(f"\n✅ Generated {len(timeline)} timeline entries from {len(all_splits)} text splits")
        return timeline
    
    def _download_images_for_split(self, split: TextSplit, video_title: str, 
                                  count: int) -> List[str]:
        """
        Download images for a text split.
        
        Args:
            split: TextSplit object
            video_title: Video title for path organization
            count: Number of images to download
            
        Returns:
            List of image paths for the timeline
        """
        if not split.keywords:
            print("    No keywords found, skipping image search")
            return []
        
        # Try different search strategies
        search_queries = self._generate_search_queries(split.keywords)
        downloaded_images = []
        
        for query in search_queries:
            if len(downloaded_images) >= count:
                break
            
            # Search for images
            search_results = self.brave_client.search_images(query, count * 2)
            
            # Download the best results
            for image_info in search_results:
                if len(downloaded_images) >= count:
                    break
                
                # Generate filename
                filename = self.brave_client.get_image_filename(
                    image_info, split.original_segment_index, split.split_index, query
                )
                
                file_path = self.output_dir / video_title / filename
                
                # Skip if already exists
                if file_path.exists():
                    relative_path = f"./{video_title}/{filename}"
                    downloaded_images.append(relative_path)
                    print(f"    Using existing: {filename}")
                    continue
                
                # Download the image
                print(f"    Downloading: {filename}")
                if self.brave_client.download_image(image_info['url'], str(file_path)):
                    relative_path = f"./{video_title}/{filename}"
                    downloaded_images.append(relative_path)
                    self.stats['images_downloaded'] += 1
                else:
                    self.stats['images_failed'] += 1
        
        print(f"    Downloaded {len(downloaded_images)} images")
        return downloaded_images
    
    def _generate_search_queries(self, keywords: List[str]) -> List[str]:
        """
        Generate search queries from keywords.
        
        Args:
            keywords: List of keywords
            
        Returns:
            List of search queries in order of preference
        """
        if not keywords:
            return ["abstract art"]
        
        queries = []
        
        # Single important keywords (longer ones first)
        important_keywords = sorted([kw for kw in keywords if len(kw) > 3], 
                                  key=len, reverse=True)
        queries.extend(important_keywords[:3])
        
        # Combinations of 2-3 keywords
        if len(keywords) >= 2:
            # Best 2-word combinations
            for i in range(min(2, len(keywords))):
                for j in range(i + 1, min(4, len(keywords))):
                    queries.append(f"{keywords[i]} {keywords[j]}")
        
        # Fallback queries
        if not queries:
            queries = ["nature", "landscape", "abstract"]
        
        return queries[:5]  # Limit to 5 queries max
    
    def save_timeline(self, timeline: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save timeline to JSON file.
        
        Args:
            timeline: Timeline data
            output_path: Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Timeline saved to: {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['images_downloaded'] / 
                (self.stats['images_downloaded'] + self.stats['images_failed'])
                if (self.stats['images_downloaded'] + self.stats['images_failed']) > 0 
                else 0
            ) * 100
        }
    
    def preview_timeline(self, timeline: List[Dict[str, Any]], max_items: int = 10) -> None:
        """
        Print timeline preview.
        
        Args:
            timeline: Timeline data
            max_items: Maximum items to show
        """
        print(f"\n👀 Timeline Preview (showing first {max_items} items):")
        print("=" * 50)
        
        for i, segment in enumerate(timeline[:max_items]):
            duration = (
                self.text_splitter._time_to_seconds(segment['end']) - 
                self.text_splitter._time_to_seconds(segment['start'])
            )
            
            print(f"\nSegment {i + 1}:")
            print(f"  Time: {segment['start']} → {segment['end']} ({duration:.1f}s)")
            print(f"  Images: {len(segment['image'])}")
            
            if segment['image']:
                for img_path in segment['image']:
                    print(f"    - {Path(img_path).name}")
        
        if len(timeline) > max_items:
            print(f"\n... and {len(timeline) - max_items} more segments")
        
        # Show statistics
        stats = self.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Total segments: {stats['total_segments']}")
        print(f"  Total splits: {stats['total_splits']}")
        print(f"  Images downloaded: {stats['images_downloaded']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
