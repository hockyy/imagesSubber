#!/usr/bin/env python3
"""
Web-based SRT Image Timeline Generator

A Flask web application for creating image timelines from SRT files
using Brave Search API with image selection and download functionality.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
import json
import threading
from pathlib import Path
import uuid
from datetime import datetime

from srt_parser import SRTParser
from text_splitter import SmartTextSplitter
from brave_image_client import BraveImageClient
import urllib.parse
from xml.sax.saxutils import escape

app = Flask(__name__)
app.secret_key = 'srt-timeline-generator-2024'

# Global storage for session data
sessions = {}
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
DOWNLOAD_FOLDER = 'download'
STATIC_FOLDER = 'static'

# Create directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, DOWNLOAD_FOLDER, STATIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

class TimelineSession:
    """Manages a user session for timeline generation."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.srt_file_path = None
        self.video_title = ""
        self.brave_api_key = ""
        self.text_splits = []
        self.selected_images = {}  # {split_index: [image_info_list]}
        self.search_results = {}   # {split_index: [image_results]}
        
        # Components
        self.srt_parser = SRTParser()
        self.text_splitter = SmartTextSplitter()
        self.brave_client = None
        
        self.created_at = datetime.now()
        
    def setup_brave_client(self, api_key):
        """Setup Brave API client."""
        self.brave_api_key = api_key
        self.brave_client = BraveImageClient(api_key)
        
    def process_srt_file(self, file_path, video_title):
        """Process SRT file and create text splits."""
        self.srt_file_path = file_path
        self.video_title = video_title
        
        # Parse SRT file
        subtitle_entries = self.srt_parser.parse_srt_file(file_path)
        if not subtitle_entries:
            raise ValueError("No subtitle entries found in SRT file")
        
        # Create text splits
        self.text_splits = []
        for i, entry in enumerate(subtitle_entries):
            splits = self.text_splitter.split_subtitle_text(
                entry.text, entry.start_time, entry.end_time, i
            )
            self.text_splits.extend(splits)
        
        return len(subtitle_entries), len(self.text_splits)

def time_to_seconds(time_str):
    """Convert HH:MM:SS,mmm or HH:MM:SS.mmm to seconds."""
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds

def seconds_to_fcpxml_time(seconds):
    """Convert seconds to FCPXML time format (rational number)."""
    # FCPXML uses rational time: numerator/denominator
    # Common timebase is 1001/30000s for 29.97fps or 1/25s for 25fps
    # We'll use 1/1000s for millisecond precision
    numerator = int(seconds * 1000)
    return f"{numerator}/1000s"

def seconds_to_frames(seconds, fps=24):
    """Convert seconds to frames."""
    return int(seconds * fps)

def time_range_to_offset_duration(start_seconds, end_seconds, fps=24):
    """Convert [start, end] time range to (offset_frames, duration_frames)."""
    start_frames = seconds_to_frames(start_seconds, fps)
    end_frames = seconds_to_frames(end_seconds, fps)
    duration_frames = end_frames - start_frames
    return start_frames, duration_frames

def insert_video_clip(asset_id, clip_name, offset_frames, duration_frames):
    """Generate FCPXML video clip element."""
    return f'''
                        <video ref="{asset_id}" start="0/1s" offset="{offset_frames}/24s" duration="{duration_frames}/24s" name="{escape(clip_name)}" enabled="1">
                            <adjust-transform scale="1 1" position="0 0" anchor="0 0"/>
                        </video>'''

def insert_gap_clip(offset_frames, duration_frames):
    """Generate FCPXML gap element."""
    return f'''
                        <gap start="0/1s" offset="{offset_frames}/24s" duration="{duration_frames}/24s" name="Gap"/>'''

class TimelineClip:
    """Represents a timeline clip with start/end times and image path."""
    def __init__(self, start_seconds, end_seconds, image_path, asset_id):
        self.start = start_seconds
        self.end = end_seconds
        self.image_path = image_path
        self.asset_id = asset_id
        self.clip_name = Path(image_path).stem
    
    def duration(self):
        return self.end - self.start
    
    def start_frames(self, fps=24):
        return seconds_to_frames(self.start, fps)
    
    def duration_frames(self, fps=24):
        return seconds_to_frames(self.duration(), fps)
    
    def __repr__(self):
        return f"TimelineClip({self.start:.2f}-{self.end:.2f}s, {self.clip_name})"

def generate_fcpxml_timeline(timeline, video_title):
    """Generate FCPXML content from timeline data matching the provided format."""
    
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
            fcpxml_content += insert_gap_clip(current_timeline_position, gap_duration_frames)
            current_timeline_position += gap_duration_frames
        duration_frames = clip['end_frames'] - clip['start_frames'] + 1
        # Add the video clip
        fcpxml_content += insert_video_clip(
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



@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_srt():
    """Upload SRT file and create session."""
    try:
        # Create new session
        session_id = str(uuid.uuid4())
        session = TimelineSession(session_id)
        
        # Get form data
        video_title = request.form.get('video_title', '').strip()
        brave_api_key = request.form.get('brave_api_key', '').strip()
        
        if not video_title:
            return jsonify({'error': 'Video title is required'}), 400
        
        if not brave_api_key:
            return jsonify({'error': 'Brave API key is required'}), 400
        
        # Handle file upload
        if 'srt_file' not in request.files:
            return jsonify({'error': 'No SRT file uploaded'}), 400
        
        file = request.files['srt_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.srt'):
            return jsonify({'error': 'File must be an SRT file'}), 400
        
        # Save uploaded file
        filename = f"{session_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Setup session
        session.setup_brave_client(brave_api_key)
        
        # Process SRT file
        segments_count, splits_count = session.process_srt_file(file_path, video_title)
        
        # Store session
        sessions[session_id] = session
        
        return jsonify({
            'session_id': session_id,
            'video_title': video_title,
            'segments_count': segments_count,
            'splits_count': splits_count,
            'message': f'Successfully processed {segments_count} segments into {splits_count} splits'
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/<session_id>')
def get_timeline(session_id):
    """Get timeline splits for a session."""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    timeline_data = []
    for i, split in enumerate(session.text_splits):
        selected_count = len(session.selected_images.get(i, []))
        
        timeline_data.append({
            'index': i,
            'start_time': split.start_time,
            'end_time': split.end_time,
            'text': split.text,
            'keywords': split.keywords,
            'selected_images_count': selected_count,
            'has_search_results': i in session.search_results
        })
    
    return jsonify({
        'session_id': session_id,
        'video_title': session.video_title,
        'timeline': timeline_data
    })

@app.route('/api/search/<session_id>/<int:split_index>', methods=['POST'])
def search_images(session_id, split_index):
    """Search for images for a specific split."""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    if split_index >= len(session.text_splits):
        return jsonify({'error': 'Split index out of range'}), 400
    
    if not session.brave_client:
        return jsonify({'error': 'Brave API client not initialized'}), 500
    
    try:
        split = session.text_splits[split_index]
        
        # Get custom keywords from request if provided
        data = request.get_json() if request.is_json else {}
        custom_keywords = data.get('custom_keywords', [])
        
        # Use custom keywords if provided, otherwise use original split keywords
        keywords_to_use = custom_keywords if custom_keywords else split.keywords
        
        # Combine keywords into search query (no limit)
        if keywords_to_use:
            combined_query = " ".join(keywords_to_use)
        else:
            combined_query = "abstract art"
        
        print(f"Searching for split {split_index}: '{combined_query}' (custom: {bool(custom_keywords)})")
        
        # Search for images
        results = session.brave_client.search_images(combined_query, count=12)
        
        # Store results
        session.search_results[split_index] = results
        
        return jsonify({
            'split_index': split_index,
            'query': combined_query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/select/<session_id>/<int:split_index>', methods=['POST'])
def select_images(session_id, split_index):
    """Select/deselect images for a split."""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    try:
        data = request.get_json()
        selected_image_ids = data.get('selected_image_ids', [])
        
        # Get search results for this split
        if split_index not in session.search_results:
            return jsonify({'error': 'No search results found for this split'}), 400
        
        # Find selected images
        selected_images = []
        for result in session.search_results[split_index]:
            if result['id'] in selected_image_ids:
                selected_images.append(result)
        
        # Store selections
        session.selected_images[split_index] = selected_images
        
        return jsonify({
            'split_index': split_index,
            'selected_count': len(selected_images),
            'selected_images': selected_images
        })
        
    except Exception as e:
        print(f"Selection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<session_id>', methods=['POST'])
def export_timeline(session_id):
    """Export timeline to JSON and download selected images."""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    try:
        # Get persistent selections from frontend
        data = request.get_json() if request.is_json else {}
        persistent_selections = data.get('persistent_selections', {})
        # Create both output and download directories
        session_output_dir = Path(OUTPUT_FOLDER) / session_id / session.video_title
        session_download_dir = Path(DOWNLOAD_FOLDER) / session.video_title
        session_output_dir.mkdir(parents=True, exist_ok=True)
        session_download_dir.mkdir(parents=True, exist_ok=True)
        
        timeline = []
        downloaded_images = []
        
        for i, split in enumerate(session.text_splits):
            # Use persistent selections if provided, otherwise fall back to session.selected_images
            selected_imgs = []
            if str(i) in persistent_selections:
                selected_imgs = persistent_selections[str(i)]
            else:
                selected_imgs = session.selected_images.get(i, [])
            
            # Download images and create file paths
            image_paths = []
            for j, img_info in enumerate(selected_imgs):
                # Generate filename
                filename = session.brave_client.get_image_filename(
                    img_info, split.original_segment_index, split.split_index, 
                    " ".join(split.keywords[:2])
                )
                
                # Download to both locations
                output_file_path = session_output_dir / filename
                download_file_path = session_download_dir / filename
                
                # Use full_url for downloading the actual image
                download_url = img_info.get('full_url', img_info['url'])
                
                # Download image to both locations
                download_success = False
                if session.brave_client.download_image(download_url, str(output_file_path)):
                    # Copy to download folder as well
                    try:
                        import shutil
                        shutil.copy2(str(output_file_path), str(download_file_path))
                        download_success = True
                    except Exception as e:
                        print(f"Failed to copy to download folder: {e}")
                        # Still consider it successful if output folder worked
                        download_success = True
                
                if download_success:
                    # Use absolute path for JSON
                    absolute_path = str(download_file_path.resolve())
                    image_paths.append(absolute_path)
                    downloaded_images.append(filename)
                    print(f"Downloaded: {filename} -> {download_file_path}")
                else:
                    print(f"Failed to download: {filename}")
            
            # Create timeline entry
            timeline_entry = {
                "start": split.start_time,
                "end": split.end_time,
                "image": image_paths
            }
            timeline.append(timeline_entry)
        
        # Save timeline JSON to both locations
        timeline_file = session_output_dir.parent / f"{session.video_title}_timeline.json"
        download_timeline_file = Path(DOWNLOAD_FOLDER) / f"{session.video_title}_timeline.json"
        
        with open(timeline_file, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        with open(download_timeline_file, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        # Generate FCPXML timeline
        fcpxml_content = generate_fcpxml_timeline(timeline, session.video_title)
        fcpxml_file = session_output_dir.parent / f"{session.video_title}_timeline.fcpxml"
        download_fcpxml_file = Path(DOWNLOAD_FOLDER) / f"{session.video_title}_timeline.fcpxml"
        
        with open(fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        with open(download_fcpxml_file, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        return jsonify({
            'timeline_file': str(timeline_file.relative_to(OUTPUT_FOLDER)),
            'download_timeline_file': str(download_timeline_file.relative_to(DOWNLOAD_FOLDER)),
            'fcpxml_file': str(fcpxml_file.relative_to(OUTPUT_FOLDER)),
            'download_fcpxml_file': str(download_fcpxml_file.relative_to(DOWNLOAD_FOLDER)),
            'images_downloaded': len(downloaded_images),
            'total_entries': len(timeline),
            'output_directory': str(session_output_dir.relative_to(OUTPUT_FOLDER)),
            'download_directory': str(session_download_dir.relative_to(DOWNLOAD_FOLDER)),
            'downloaded_files': downloaded_images
        })
        
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/output/<path:filename>')
def download_file(filename):
    """Serve downloaded files."""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/download/<path:filename>')
def serve_download_file(filename):
    """Serve files from download folder."""
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route('/timeline')
def timeline_page():
    """Timeline editing page."""
    return render_template('timeline.html')

if __name__ == '__main__':
    print("🚀 Starting SRT Image Timeline Generator Web App...")
    print("📋 Server will be available at: http://localhost:5000")
    print("📁 Files will be saved to: ./output/")
    print("⏹️  Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
