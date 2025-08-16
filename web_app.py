#!/usr/bin/env python3
"""
Web-based SRT Image Timeline Generator

A Flask web application for creating image timelines from SRT files
using Brave Search API with image selection and download functionality.
"""

from flask import Flask
import os

from web.session_manager import WebSessionManager
from web.routes import WebRoutes

app = Flask(__name__)
app.secret_key = 'srt-timeline-generator-2024'

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
DOWNLOAD_FOLDER = 'download'
STATIC_FOLDER = 'static'

# Create directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, DOWNLOAD_FOLDER, STATIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Initialize components
session_manager = WebSessionManager()
web_routes = WebRoutes(app, session_manager, UPLOAD_FOLDER, OUTPUT_FOLDER, DOWNLOAD_FOLDER)

if __name__ == '__main__':
    print("🚀 Starting SRT Image Timeline Generator Web App...")
    print("📋 Server will be available at: http://localhost:5000")
    print("📁 Files will be saved to: ./output/")
    print("⏹️  Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
