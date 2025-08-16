"""
Flask routes for the SRT Image Timeline Generator web app.
Contains all API endpoints and route handlers.
"""

import os
import json
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

from web_session_manager import WebSessionManager
from fcpxml_generator import FCPXMLGenerator


class WebRoutes:
    """Handles all web routes for the Flask application."""
    
    def __init__(self, app: Flask, session_manager: WebSessionManager, 
                 upload_folder: str, output_folder: str, download_folder: str):
        self.app = app
        self.session_manager = session_manager
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        self.download_folder = download_folder
        self.fcpxml_generator = FCPXMLGenerator()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all Flask routes."""
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/api/upload', 'upload_srt', self.upload_srt, methods=['POST'])
        self.app.add_url_rule('/api/timeline/<session_id>', 'get_timeline', self.get_timeline)
        self.app.add_url_rule('/api/search/<session_id>/<int:split_index>', 'search_images', 
                             self.search_images, methods=['POST'])
        self.app.add_url_rule('/api/select/<session_id>/<int:split_index>', 'select_images', 
                             self.select_images, methods=['POST'])
        self.app.add_url_rule('/api/export/<session_id>', 'export_timeline', 
                             self.export_timeline, methods=['POST'])
        self.app.add_url_rule('/output/<path:filename>', 'download_file', self.download_file)
        self.app.add_url_rule('/download/<path:filename>', 'serve_download_file', self.serve_download_file)
        self.app.add_url_rule('/timeline', 'timeline_page', self.timeline_page)
    
    def index(self):
        """Main page."""
        return render_template('index.html')
    
    def upload_srt(self):
        """Upload SRT file and create session."""
        try:
            # Create new session
            session = self.session_manager.create_session()
            
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
            filename = f"{session.session_id}_{file.filename}"
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            
            # Setup session
            session.setup_brave_client(brave_api_key)
            
            # Process SRT file
            segments_count, splits_count = session.process_srt_file(file_path, video_title)
            
            return jsonify({
                'session_id': session.session_id,
                'video_title': video_title,
                'segments_count': segments_count,
                'splits_count': splits_count,
                'message': f'Successfully processed {segments_count} segments into {splits_count} splits'
            })
            
        except Exception as e:
            print(f"Upload error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_timeline(self, session_id: str):
        """Get timeline splits for a session."""
        if not self.session_manager.session_exists(session_id):
            return jsonify({'error': 'Session not found'}), 404
        
        session = self.session_manager.get_session(session_id)
        
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
    
    def search_images(self, session_id: str, split_index: int):
        """Search for images for a specific split."""
        if not self.session_manager.session_exists(session_id):
            return jsonify({'error': 'Session not found'}), 404
        
        session = self.session_manager.get_session(session_id)
        
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
    
    def select_images(self, session_id: str, split_index: int):
        """Select/deselect images for a split."""
        if not self.session_manager.session_exists(session_id):
            return jsonify({'error': 'Session not found'}), 404
        
        session = self.session_manager.get_session(session_id)
        
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
    
    def export_timeline(self, session_id: str):
        """Export timeline to JSON and download selected images."""
        if not self.session_manager.session_exists(session_id):
            return jsonify({'error': 'Session not found'}), 404
        
        session = self.session_manager.get_session(session_id)
        
        try:
            # Get persistent selections from frontend
            data = request.get_json() if request.is_json else {}
            persistent_selections = data.get('persistent_selections', {})
            
            # Create both output and download directories
            session_output_dir = Path(self.output_folder) / session_id / session.video_title
            session_download_dir = Path(self.download_folder) / session.video_title
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
            download_timeline_file = Path(self.download_folder) / f"{session.video_title}_timeline.json"
            
            with open(timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline, f, indent=2, ensure_ascii=False)
            
            with open(download_timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline, f, indent=2, ensure_ascii=False)
            
            # Generate FCPXML timeline
            fcpxml_content = self.fcpxml_generator.generate_fcpxml_timeline(timeline, session.video_title)
            fcpxml_file = session_output_dir.parent / f"{session.video_title}_timeline.fcpxml"
            download_fcpxml_file = Path(self.download_folder) / f"{session.video_title}_timeline.fcpxml"
            
            with open(fcpxml_file, 'w', encoding='utf-8') as f:
                f.write(fcpxml_content)
            
            with open(download_fcpxml_file, 'w', encoding='utf-8') as f:
                f.write(fcpxml_content)
            
            return jsonify({
                'timeline_file': str(timeline_file.relative_to(Path(self.output_folder))),
                'download_timeline_file': str(download_timeline_file.relative_to(Path(self.download_folder))),
                'fcpxml_file': str(fcpxml_file.relative_to(Path(self.output_folder))),
                'download_fcpxml_file': str(download_fcpxml_file.relative_to(Path(self.download_folder))),
                'images_downloaded': len(downloaded_images),
                'total_entries': len(timeline),
                'output_directory': str(session_output_dir.relative_to(Path(self.output_folder))),
                'download_directory': str(session_download_dir.relative_to(Path(self.download_folder))),
                'downloaded_files': downloaded_images
            })
            
        except Exception as e:
            print(f"Export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def download_file(self, filename: str):
        """Serve downloaded files."""
        return send_from_directory(self.output_folder, filename)
    
    def serve_download_file(self, filename: str):
        """Serve files from download folder."""
        return send_from_directory(self.download_folder, filename)
    
    def timeline_page(self):
        """Timeline editing page."""
        return render_template('timeline.html')
