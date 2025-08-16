"""
Timeline operations module for timeline generation.
Handles saving, previewing, and other timeline operations.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

from core.text_splitter import SmartTextSplitter
from utils.statistics_tracker import StatisticsTracker


class TimelineOperations:
    """Handles timeline operations like saving and previewing."""
    
    def __init__(self, text_splitter: SmartTextSplitter, stats_tracker: StatisticsTracker):
        """
        Initialize timeline operations.
        
        Args:
            text_splitter: Text splitter instance for time calculations
            stats_tracker: Statistics tracker instance
        """
        self.text_splitter = text_splitter
        self.stats_tracker = stats_tracker
    
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
        stats = self.stats_tracker.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Total segments: {stats['total_segments']}")
        print(f"  Total splits: {stats['total_splits']}")
        print(f"  Images downloaded: {stats['images_downloaded']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
