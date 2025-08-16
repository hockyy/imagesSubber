#!/usr/bin/env python3
"""
SRT Image Timeline Generator

Clean, focused application using Brave Search API with smart text splitting.
Splits subtitle text intelligently and downloads relevant images.
"""

import argparse
import sys
import os
from pathlib import Path

from timeline_generator import TimelineGenerator

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Generate image timeline from SRT files using Brave Search API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
How it works:
  1. Parses SRT subtitle file
  2. Splits each subtitle based on duration (ceil(duration/3s))
  3. Extracts keywords from each split
  4. Searches Brave Image API for relevant images
  5. Downloads images and creates JSON timeline

Text Splitting:
  - Based on duration only: ceil(duration / 3 seconds)  
  - Example: "I like to eat an apple" (6s) → 2 splits:
    * "I like to" (0-3s)
    * "eat an apple" (3-6s)

Brave Search API:
  Get your API key at: https://api-dashboard.search.brave.com/app/documentation/image-search/get-started
  - Free tier available
  - Up to 20 images per search
  - High-quality results

Examples:
  # Basic usage
  python main.py movie.srt "My Movie" --api-key YOUR_BRAVE_API_KEY
  
  # With preview and custom settings
  python main.py movie.srt "My Movie" --api-key YOUR_KEY \\
    --images-per-split 3 --preview --output custom_timeline.json
  
  # Show statistics
  python main.py movie.srt "My Movie" --api-key YOUR_KEY --stats
        """
    )
    
    # Required arguments
    parser.add_argument(
        'srt_file',
        help='Path to the SRT subtitle file'
    )
    
    parser.add_argument(
        'video_title',
        help='Title of the video (used for organizing downloaded images)'
    )
    
    parser.add_argument(
        '--api-key',
        required=True,
        help='Brave Search API key (get from https://api-dashboard.search.brave.com/)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output', '-o',
        default='timeline.json',
        help='Output JSON file path (default: timeline.json)'
    )
    
    parser.add_argument(
        '--images-per-split',
        type=int,
        default=2,
        help='Number of images to download per text split (default: 2)'
    )
    
    parser.add_argument(
        '--image-dir',
        default='images',
        help='Directory to save downloaded images (default: images)'
    )
    
    # Display options
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Show timeline preview after generation'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed statistics'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and split text without downloading images'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        if not os.path.exists(args.srt_file):
            print(f"❌ Error: SRT file not found: {args.srt_file}")
            sys.exit(1)
        
        if args.images_per_split < 1 or args.images_per_split > 10:
            print("❌ Error: images-per-split must be between 1 and 10")
            sys.exit(1)
        
        print("🎬 SRT Image Timeline Generator")
        print("=" * 35)
        print(f"📝 SRT File: {args.srt_file}")
        print(f"🎥 Video: {args.video_title}")
        print(f"🖼️  Images per split: {args.images_per_split}")
        
        if args.dry_run:
            print("🧪 DRY RUN MODE - No images will be downloaded")
            # TODO: Implement dry run mode
            print("❌ Dry run mode not implemented yet")
            sys.exit(1)
        
        # Initialize timeline generator
        print(f"\n🔑 Initializing Brave Search API...")
        timeline_generator = TimelineGenerator(
            brave_api_key=args.api_key,
            output_dir=args.image_dir
        )
        
        # Generate timeline
        print(f"\n🚀 Starting timeline generation...")
        timeline = timeline_generator.generate_timeline(
            srt_path=args.srt_file,
            video_title=args.video_title,
            images_per_split=args.images_per_split
        )
        
        if not timeline:
            print("❌ No timeline generated")
            sys.exit(1)
        
        # Save timeline
        timeline_generator.save_timeline(timeline, args.output)
        
        # Show preview if requested
        if args.preview:
            timeline_generator.preview_timeline(timeline)
        
        # Show statistics if requested
        if args.stats:
            stats = timeline_generator.get_statistics()
            print(f"\n📊 Detailed Statistics:")
            print(f"  Original segments: {stats['total_segments']}")
            print(f"  Text splits created: {stats['total_splits']}")
            print(f"  Images downloaded: {stats['images_downloaded']}")
            print(f"  Download failures: {stats['images_failed']}")
            print(f"  Success rate: {stats['success_rate']:.1f}%")
            print(f"  Average splits per segment: {stats['total_splits'] / stats['total_segments']:.1f}")
        
        # Final summary
        print(f"\n✅ Timeline generation completed!")
        print(f"📄 Timeline: {args.output} ({len(timeline)} entries)")
        print(f"📁 Images: {args.image_dir}/{args.video_title}/")
        
        # Show usage tip
        print(f"\n💡 Your timeline JSON is ready to use!")
        print(f"   Each entry has: start time, end time, and image paths")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.stats:  # Show more details in verbose mode
            import traceback
            traceback.print_exc()
        sys.exit(1)

def show_examples():
    """Show detailed usage examples."""
    examples = """
🎬 SRT Image Timeline Generator - Examples
==========================================

BASIC USAGE:
python main.py movie.srt "My Movie" --api-key YOUR_BRAVE_API_KEY

TEXT SPLITTING EXAMPLE:
Original subtitle (6 seconds): "I like to eat an apple"
→ Split 1 (0-2s): "I like" → search for "like" images
→ Split 2 (2-4s): "to eat" → search for "eat" images  
→ Split 3 (4-6s): "an apple" → search for "apple" images

ADVANCED OPTIONS:
# More images per split
python main.py movie.srt "My Movie" --api-key KEY --images-per-split 3

# Custom output and preview
python main.py movie.srt "My Movie" --api-key KEY \\
  --output custom_timeline.json --preview --stats

# Custom image directory
python main.py movie.srt "My Movie" --api-key KEY \\
  --image-dir /path/to/images

OUTPUT FORMAT:
[
  {
    "start": "00:00:01,000",
    "end": "00:00:03,000", 
    "image": ["./My Movie/seg000_split0_like_abc123.jpg", "./My Movie/seg000_split0_enjoy_def456.jpg"]
  },
  {
    "start": "00:00:03,000",
    "end": "00:00:05,000",
    "image": ["./My Movie/seg000_split1_eat_ghi789.jpg"]
  }
]

GETTING BRAVE API KEY:
1. Go to: https://api-dashboard.search.brave.com/
2. Sign up for free account
3. Subscribe to Image Search API (free tier available)
4. Get your API key from dashboard
5. Use with --api-key parameter
"""
    print(examples)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--examples':
        show_examples()
    else:
        main()
