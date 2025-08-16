"""
Statistics tracker module for timeline generation.
Tracks and provides statistics about the timeline generation process.
"""

from typing import Dict, Any


class StatisticsTracker:
    """Tracks statistics during timeline generation."""
    
    def __init__(self):
        """Initialize statistics tracker."""
        self.stats = {
            'total_segments': 0,
            'total_splits': 0,
            'images_downloaded': 0,
            'images_failed': 0
        }
    
    def increment_images_downloaded(self, count: int = 1) -> None:
        """Increment downloaded images count."""
        self.stats['images_downloaded'] += count
    
    def increment_images_failed(self, count: int = 1) -> None:
        """Increment failed images count."""
        self.stats['images_failed'] += count
    
    def set_segments_count(self, count: int) -> None:
        """Set total segments count."""
        self.stats['total_segments'] = count
    
    def set_splits_count(self, count: int) -> None:
        """Set total splits count."""
        self.stats['total_splits'] = count
    
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
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.stats = {
            'total_segments': 0,
            'total_splits': 0,
            'images_downloaded': 0,
            'images_failed': 0
        }
