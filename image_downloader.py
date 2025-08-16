"""
Image downloader module for timeline generation.
Handles downloading images for text splits using Brave Search API.
"""

from typing import List, Dict, Any
from pathlib import Path

from text_splitter import TextSplit
from brave_image_client import BraveImageClient
from statistics_tracker import StatisticsTracker


class ImageDownloader:
    """Handles downloading images for text splits."""
    
    def __init__(self, brave_client: BraveImageClient, output_dir: Path, stats_tracker: StatisticsTracker):
        """
        Initialize the image downloader.
        
        Args:
            brave_client: Brave Search API client
            output_dir: Base directory for saving images
            stats_tracker: Statistics tracker for recording download results
        """
        self.brave_client = brave_client
        self.output_dir = output_dir
        self.stats_tracker = stats_tracker
        
    def download_images_for_split(self, split: TextSplit, video_title: str, 
                                 count: int, search_queries: List[str]) -> List[str]:
        """
        Download images for a text split.
        
        Args:
            split: TextSplit object
            video_title: Video title for path organization
            count: Number of images to download
            search_queries: List of search queries to try
            
        Returns:
            List of image paths for the timeline
        """
        if not split.keywords:
            print("    No keywords found, skipping image search")
            return []
        
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
                    self.stats_tracker.increment_images_downloaded()
                else:
                    print(f"    Failed to download: {filename}")
                    self.stats_tracker.increment_images_failed()
        
        print(f"    Downloaded {len(downloaded_images)} images")
        return downloaded_images
