"""
FCPXML generator for creating Final Cut Pro timeline files.
Converts timeline data to FCPXML format.
"""

from typing import List, Dict, Any
from pathlib import Path
from xml.sax.saxutils import escape

from time_utils import time_to_seconds, seconds_to_frames


class TimelineClip:
    """Represents a timeline clip with start/end times and image path."""
    
    def __init__(self, start_seconds: float, end_seconds: float, image_path: str, asset_id: str):
        self.start = start_seconds
        self.end = end_seconds
        self.image_path = image_path
        self.asset_id = asset_id
        self.clip_name = Path(image_path).stem
    
    def duration(self) -> float:
        """Get clip duration in seconds."""
        return self.end - self.start
    
    def start_frames(self, fps: int = 24) -> int:
        """Get start time in frames."""
        return seconds_to_frames(self.start, fps)
    
    def duration_frames(self, fps: int = 24) -> int:
        """Get duration in frames."""
        return seconds_to_frames(self.duration(), fps)
    
    def __repr__(self) -> str:
        return f"TimelineClip({self.start:.2f}-{self.end:.2f}s, {self.clip_name})"


class FCPXMLGenerator:
    """Generates FCPXML content from timeline data."""
    
    @staticmethod
    def insert_video_clip(asset_id: str, clip_name: str, offset_frames: int, duration_frames: int) -> str:
        """Generate FCPXML video clip element."""
        return f'''
                        <video ref="{asset_id}" start="0/1s" offset="{offset_frames}/24s" duration="{duration_frames}/24s" name="{escape(clip_name)}" enabled="1">
                            <adjust-transform scale="1 1" position="0 0" anchor="0 0"/>
                        </video>'''

    @staticmethod
    def insert_gap_clip(offset_frames: int, duration_frames: int) -> str:
        """Generate FCPXML gap element."""
        return f'''
                        <gap start="0/1s" offset="{offset_frames}/24s" duration="{duration_frames}/24s" name="Gap"/>'''

    def generate_fcpxml_timeline(self, timeline: List[Dict[str, Any]], video_title: str) -> str:
        """
        Generate FCPXML content from timeline data.
        
        Args:
            timeline: Timeline data as list of segments
            video_title: Title of the video project
            
        Returns:
            Complete FCPXML content as string
        """
        # Calculate total duration in 24fps frames
        total_duration = 0
        if timeline:
            last_entry = timeline[-1]
            total_duration = time_to_seconds(last_entry['end'])
        
        total_duration_frames = int(total_duration * 24)  # Convert to 24fps frames
        
        # Start building FCPXML
        fcpxml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.13">
    <resources>
        <format width="1920" id="r0" height="1080" name="FFVideoFormatRateUndefined" frameDuration="1/24s"/>'''
        
        # Add asset resources for each unique image
        asset_counter = 1
        image_assets = {}
        
        for entry in timeline:
            for image_path in entry.get('image', []):
                if image_path not in image_assets:
                    asset_id = f"r{asset_counter}"
                    image_name = Path(image_path).stem
                    
                    # Convert Windows path to proper file:// URL format
                    if image_path.startswith('C:'):
                        file_url = f"file://localhost/{image_path.replace('\\', '/')}"
                    else:
                        file_url = Path(image_path).as_uri()
                    
                    fcpxml_content += f'''
        <asset start="0/1s" id="{asset_id}" duration="0/1s" name="{escape(image_name)}" hasVideo="1">
            <media-rep src="{escape(file_url)}" kind="original-media"/>
        </asset>'''
                    
                    image_assets[image_path] = asset_id
                    asset_counter += 1
        
        # Step 1: Precompute all clips, ignoring gaps
        all_clips = []
        
        for entry in timeline:
            start_seconds = time_to_seconds(entry['start'])
            end_seconds = time_to_seconds(entry['end'])
            images = entry.get('image', [])
            
            if images:
                # Divide segment duration equally among images
                segment_duration = end_seconds - start_seconds
                image_duration = segment_duration / len(images)
                
                # Create clips for each image
                for idx, image_path in enumerate(images):
                    asset_id = image_assets.get(image_path)
                    if asset_id:
                        clip_start = start_seconds + (idx * image_duration)
                        clip_end = clip_start + image_duration
                        
                        clip = TimelineClip(clip_start, clip_end, image_path, asset_id)
                        all_clips.append(clip)
        
        # Step 2: Sort clips by start time
        all_clips.sort(key=lambda clip: clip.end)
        
        # Step 3: Fix overlapping segments
        for i in range(1, len(all_clips)):
            if all_clips[i].start < all_clips[i-1].end:
                # Clip overlaps with previous, adjust start time
                all_clips[i].start = max(all_clips[i].start, all_clips[i-1].end)
                
                # If start >= end after adjustment, remove this clip
                if all_clips[i].start >= all_clips[i].end:
                    all_clips[i] = None
        
        # Remove None clips (clips that were eliminated due to overlap)
        all_clips = [clip for clip in all_clips if clip is not None]
        
        print(f"Generated {len(all_clips)} clips after overlap resolution:")
        for clip in all_clips:
            print(f"  {clip}")
        
        # Step 4: Generate FCPXML with clips and gaps
        fcpxml_content += f'''
    </resources>
    <library>
        <event name="{escape(video_title)}">
            <project name="{escape(video_title)}">
                <sequence tcStart="0/1s" duration="{total_duration_frames}/24s" format="r0" tcFormat="NDF">
                    <spine>'''
        
        # Step 1: Convert all clips to frame-based representation
        frame_clips = []
        for clip in all_clips:
            frame_clip = {
                'start_frames': seconds_to_frames(clip.start),
                'end_frames': seconds_to_frames(clip.end),
                'asset_id': clip.asset_id,
                'clip_name': clip.clip_name,
                'image_path': clip.image_path
            }
            frame_clips.append(frame_clip)
        
        print(f"Converted to {len(frame_clips)} frame-based clips:")
        for i, clip in enumerate(frame_clips):
            print(f"  Clip {i}: {clip['start_frames']}-{clip['end_frames']} frames ({clip['clip_name']})")
        
        # Step 2: Process frame-based clips to handle small gaps
        MIN_GAP_THRESHOLD_FRAMES = 12  # 0.5 seconds at 24fps
        processed_frame_clips = []
        
        for i, clip in enumerate(frame_clips):
            if i == 0:
                # First clip, just add it
                processed_frame_clips.append(clip)
            else:
                previous_clip = processed_frame_clips[-1]
                gap_frames = clip['start_frames'] - previous_clip['end_frames'] + 1
                
                if gap_frames > 0 and gap_frames <= MIN_GAP_THRESHOLD_FRAMES:
                    # Small gap - extend previous clip to cover it
                    print(f"  Extending previous clip by {gap_frames} frames to cover small gap")
                    previous_clip['end_frames'] = clip['start_frames']
                    
                    # Add current clip
                    processed_frame_clips.append(clip)
                else:
                    # Large gap or no gap - just add current clip
                    if gap_frames > 0:
                        print(f"  Keeping gap of {gap_frames} frames ({gap_frames/24.0:.2f}s)")
                    processed_frame_clips.append(clip)
        
        print(f"After gap processing: {len(processed_frame_clips)} frame clips:")
        for i, clip in enumerate(processed_frame_clips):
            print(f"  Clip {i}: {clip['start_frames']}-{clip['end_frames']} frames ({clip['clip_name']})")
        
        # Step 3: Generate FCPXML from processed frame clips
        current_timeline_position = 0
        
        for i, clip in enumerate(processed_frame_clips):
            # Add gap if needed
            if clip['start_frames'] > current_timeline_position:
                gap_duration_frames = clip['start_frames'] - current_timeline_position
                print(f"  Adding gap: {gap_duration_frames} frames ({gap_duration_frames/24.0:.2f}s)")
                fcpxml_content += self.insert_gap_clip(current_timeline_position, gap_duration_frames)
                current_timeline_position += gap_duration_frames
            duration_frames = clip['end_frames'] - clip['start_frames'] + 1
            # Add the video clip
            fcpxml_content += self.insert_video_clip(
                clip['asset_id'], clip['clip_name'], current_timeline_position, duration_frames
            )
            current_timeline_position += duration_frames
        
        fcpxml_content += '''
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        
        return fcpxml_content
