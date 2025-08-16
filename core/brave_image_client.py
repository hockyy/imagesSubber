"""
Brave Search Image API client for downloading images.
"""

import requests
import os
import time
import hashlib
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from urllib.parse import urlparse

class BraveImageClient:
    """Client for Brave Search Image API."""
    
    def __init__(self, api_key: str, rate_limit_delay: float = 0.5):
        """
        Initialize Brave Image client.
        
        Args:
            api_key: Brave Search API subscription token
            rate_limit_delay: Delay between requests to respect rate limits
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.base_url = "https://api.search.brave.com/res/v1/images/search"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.api_key
        })
    
    def search_images(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Search for images using Brave Search API.
        
        Args:
            query: Search query (max 400 characters, 50 words)
            count: Number of images to return (max 200, default 50)
            
        Returns:
            List of image data dictionaries
        """
        try:
            # Validate query according to API limits
            if not query or not query.strip():
                print("❌ Empty query provided")
                return []
            
            # Truncate query if too long (max 400 chars)
            if len(query) > 400:
                query = query[:400]
                print(f"⚠️ Query truncated to 400 characters")
            
            # Check word count (max 50 words)
            word_count = len(query.split())
            if word_count > 50:
                words = query.split()[:50]
                query = " ".join(words)
                print(f"⚠️ Query truncated to 50 words")
            
            # Parameters based on official API documentation
            params = {
                'q': query,                        # Required: search query (max 400 chars, 50 words)
                'count': min(count, 50),          # Optional: max 200 (default 50)
                'search_lang': 'en',               # Optional: language code (default en)  
                'safesearch': 'off',            # Optional: off/strict (default strict)
                'spellcheck': True                 # Optional: boolean (default true)
            }
            
            print(f"🔍 Searching Brave: '{query}'")
            print(f"   URL: {self.base_url}")
            print(f"   Params: {params}")
            print(f"   Headers: {dict(self.session.headers)}")
            
            response = self.session.get(self.base_url, params=params)
            print(f"   Response status: {response.status_code}")
            
            # Log rate limit information from headers
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = response.headers['X-RateLimit-Remaining']
                reset = response.headers.get('X-RateLimit-Reset', 'unknown')
                print(f"   Rate limit remaining: {remaining}")
                print(f"   Rate limit resets in: {reset} seconds")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"   Raw API response keys: {list(data.keys())}")
            
            # Log the full response structure for debugging
            print(f"📋 Full API Response Debug:")
            print(f"   Response type: {type(data)}")
            if 'results' in data:
                print(f"   Results count: {len(data['results'])}")
                print(f"   First result keys: {list(data['results'][0].keys()) if data['results'] else 'No results'}")
            else:
                print(f"   No 'results' key found. Available keys: {list(data.keys())}")
                print(f"   Full response: {json.dumps(data, indent=2)[:500]}...")
            
            images = []
            results = data.get('results', [])
            
            print(f"🔍 Processing {len(results)} search results:")
            
            for i, result in enumerate(results):
                print(f"   Result {i+1}:")
                print(f"     Raw result keys: {list(result.keys())}")
                print(f"     Type: {result.get('type', 'NO_TYPE')}")
                print(f"     Title: {result.get('title', 'NO_TITLE')}")
                print(f"     URL (page): {result.get('url', 'NO_PAGE_URL')}")
                print(f"     Source: {result.get('source', 'NO_SOURCE')}")
                
                # Extract image URL from properties (not the page URL)
                properties = result.get('properties', {})
                print(f"     Properties: {properties}")
                
                # The actual image URL is in properties.url, not result.url
                image_url = properties.get('url', '') if properties else ''
                page_url = result.get('url', '')  # This is the page URL where image was found
                
                print(f"     Image URL: {image_url}")
                print(f"     Page URL: {page_url}")
                
                if not image_url:
                    print(f"     ❌ Skipping result {i+1}: No image URL found in properties")
                    continue
                    
                image_id = hashlib.md5(image_url.encode()).hexdigest()[:8]
                
                # Extract thumbnail info
                thumbnail = result.get('thumbnail', {})
                print(f"     Thumbnail: {thumbnail}")
                
                # Use thumbnail URL directly for display, full image URL for download
                thumbnail_url = thumbnail.get('src', '') if thumbnail else ''
                display_url = thumbnail_url if thumbnail_url else image_url
                
                print(f"     Thumbnail URL: {thumbnail_url}")
                print(f"     Display URL (final): {display_url}")
                print(f"     Using thumbnail: {'YES' if thumbnail_url else 'NO (using full image)'}")
                
                image_info = {
                    'id': image_id,
                    'url': display_url,  # Use thumbnail for display
                    'full_url': image_url,  # Keep full URL for download
                    'title': result.get('title', ''),
                    'source': result.get('source', ''),
                    'source_url': page_url,  # The page where image was found
                    'width': properties.get('width', 0) if properties else 0,
                    'height': properties.get('height', 0) if properties else 0,
                    'thumbnail_width': thumbnail.get('width', 0) if thumbnail else 0,
                    'thumbnail_height': thumbnail.get('height', 0) if thumbnail else 0,
                    'confidence': result.get('confidence', 'unknown'),
                    'service': 'brave'
                }
                
                print(f"     ✅ Processed image info: {image_info}")
                images.append(image_info)
            
            print(f"  📊 Final results: Found {len(images)} valid images out of {len(results)} API results")
            self._rate_limit_wait()
            return images
            
        except Exception as e:
            print(f"❌ Error searching Brave API:")
            print(f"   Query: '{query}'")
            print(f"   Error: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Print response details if available
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status code: {e.response.status_code}")
                print(f"   Response text: {e.response.text[:200]}...")
            
            import traceback
            print(f"   Full traceback:")
            traceback.print_exc()
            return []
    
    def download_image(self, image_url: str, save_path: str) -> bool:
        """
        Download an image from URL to local path.
        
        Args:
            image_url: URL of the image to download
            save_path: Local path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Download with a reasonable timeout
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"    Not an image: {content_type}")
                return False
            
            # Save the image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"    Download failed: {e}")
            return False
    
    def _rate_limit_wait(self):
        """Wait to respect rate limits."""
        time.sleep(self.rate_limit_delay)
    
    def get_image_filename(self, image_info: Dict[str, Any], segment_index: int, 
                          split_index: int, query: str) -> str:
        """
        Generate filename for downloaded image.
        
        Args:
            image_info: Image information
            segment_index: Subtitle segment index
            split_index: Split index within segment
            query: Search query used
            
        Returns:
            Generated filename
        """
        # Clean query for filename
        clean_query = ''.join(c for c in query if c.isalnum() or c in '-_')[:20]
        
        # Get extension from URL or default to jpg
        url = image_info.get('url', '')
        parsed_url = urlparse(url)
        ext = Path(parsed_url.path).suffix.lower()
        
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        
        return f"seg{segment_index:03d}_split{split_index}_{clean_query}_{image_info['id']}{ext}"
