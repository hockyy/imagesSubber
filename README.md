# SRT Image Timeline Generator

A clean, focused Python application that generates image timelines from SRT subtitle files using intelligent text splitting and [Brave Search API](https://api-dashboard.search.brave.com/app/documentation/image-search/get-started).

Features both a **web interface** for interactive image selection and a **command-line tool** for automated processing.

## 🎯 What It Does

1. **Parses SRT files** - Extracts subtitle text and timing
2. **Smart text splitting** - Breaks long subtitles into meaningful chunks
3. **Keyword extraction** - Finds relevant search terms from each chunk  
4. **Image search** - Uses Brave Search API to find matching images
5. **Timeline generation** - Creates JSON timeline with precise timing

## 🧠 Text Splitting

The app splits subtitle text based on duration:

```
Number of splits = ceil(duration_seconds / 3)
```

**Example:**
```
Original: "I like to eat an apple" (6 seconds)
Splits needed: ceil(6 / 3) = 2 splits
→ Split 1 (0-3s): "I like to" → searches for "like" images
→ Split 2 (3-6s): "eat an apple" → searches for "eat", "apple" images
```

## 🚀 Quick Start

### 1. Get Brave Search API Key
- Visit [Brave Search API Dashboard](https://api-dashboard.search.brave.com/)
- Sign up for free account
- Subscribe to Image Search API (free tier available)
- Get your API key

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Choose Your Interface

**Web Application (Recommended):**
```bash
python web_app.py
```
Then open http://localhost:5000 in your browser.

**Command Line Version:**
```bash
python main.py movie.srt "My Movie" --api-key YOUR_BRAVE_API_KEY
```

## 📖 Usage Examples

### Web Application (Recommended)
1. Start the server: `python web_app.py`
2. Open http://localhost:5000 in your browser
3. Upload your SRT file and enter video title + API key (saved in browser)
4. Review the generated timeline splits
5. Click search buttons for each split (or edit keywords first)
6. Select multiple images from search results
7. Export timeline - downloads images and creates JSON + FCPXML files in `./download/{video_title}/`

### Command Line Usage
```bash
python main.py movie.srt "My Movie" --api-key YOUR_KEY
```

### With Preview and Statistics
```bash
python main.py movie.srt "My Movie" --api-key YOUR_KEY --preview --stats
```

### Custom Settings
```bash
python main.py movie.srt "My Movie" --api-key YOUR_KEY \
  --images-per-split 3 \
  --output custom_timeline.json \
  --image-dir /path/to/images
```

### Show Examples
```bash
python main.py --examples
```

## 📋 Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `srt_file` | Path to SRT subtitle file | Required |
| `video_title` | Video title for organizing images | Required |
| `--api-key` | Brave Search API key | Required |
| `--output, -o` | Output JSON file path | `timeline.json` |
| `--images-per-split` | Images per text split (1-10) | `2` |
| `--image-dir` | Directory for downloaded images | `images` |
| `--preview` | Show timeline preview | False |
| `--stats` | Show detailed statistics | False |
| `--dry-run` | Parse without downloading | False |

## 📄 Output Format

The generated JSON timeline follows this structure:

```json
[
  {
    "start": "00:00:01,000",
    "end": "00:00:03,000",
    "image": [
      "./My Movie/seg000_split0_like_abc123.jpg",
      "./My Movie/seg000_split0_enjoy_def456.jpg"
    ]
  },
  {
    "start": "00:00:03,000", 
    "end": "00:00:05,000",
    "image": [
      "./My Movie/seg000_split1_eat_ghi789.jpg"
    ]
  }
]
```

## 🌐 Web Interface Features

The web application (`web_app.py`) provides an interactive browser-based interface:

- **📁 File Upload**: Drag & drop SRT files
- **⚙️ Configuration**: Enter API key and video title (saved in browser)
- **📋 Timeline View**: Interactive timeline with text splits and timing
- **🔍 Custom Search**: Edit keywords and search for images per segment
- **🖼️ Image Selection**: Multi-select images with thumbnails and preview
- **📤 Export**: Download timeline as JSON + FCPXML with selected images
- **💾 Persistent State**: Selections saved during session

### Web Workflow:
1. Upload SRT file and enter video title + API key
2. Review generated text splits in interactive timeline
3. Click search buttons for each timeline segment (or edit keywords first)
4. Select multiple images from search results
5. Export timeline with downloaded images to `./download/{video_title}/`

## 🏗️ Project Structure

```
subber/
├── main.py                    # Command line application entry point
├── web_app.py                # Web application entry point (recommended)
├── core/                     # Core processing modules
│   ├── __init__.py
│   ├── srt_parser.py         # SRT file parsing
│   ├── text_splitter.py      # Smart text splitting logic (with NLTK)
│   ├── brave_image_client.py # Brave Search API client
│   ├── timeline_generator.py # Main timeline generation logic
│   ├── image_downloader.py   # Image downloading and management
│   └── search_query_generator.py # Search query optimization
├── web/                      # Web application modules
│   ├── __init__.py
│   ├── session_manager.py    # User session management
│   ├── routes.py            # Flask API routes
│   └── fcpxml_generator.py  # Final Cut Pro XML export
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── time_utils.py        # Time format conversions
│   ├── statistics_tracker.py # Processing statistics
│   └── timeline_operations.py # Timeline file operations
├── templates/               # Web interface templates
│   ├── index.html          # Upload page
│   └── timeline.html       # Interactive timeline editor
├── static/                 # CSS and static assets
├── requirements.txt        # Python dependencies
├── sample.srt             # Example SRT file
└── download/              # Downloaded images and timelines
    └── {video_title}/     # Organized by video
```

## 🔧 How It Works

### 1. SRT Parsing
- Extracts subtitle entries with timing and text
- Handles standard SRT format with error tolerance

### 2. Text Splitting  
- Analyzes subtitle duration and word count
- Splits at natural boundaries (punctuation, conjunctions)
- Creates meaningful chunks for better image matching

### 3. Keyword Extraction
- Removes stopwords and short words
- Prioritizes longer, more descriptive terms
- Maintains word order for context

### 4. Image Search
- Uses Brave Search API for high-quality results
- Tries multiple search strategies per split
- Downloads images with unique filenames

### 5. Timeline Generation
- Creates precise timing for each split
- Organizes images by video title
- Generates clean JSON output

## 📊 Features

### Core Features
- ✅ **Smart text splitting** based on duration and content
- ✅ **High-quality images** from Brave Search API
- ✅ **Organized file structure** by video title
- ✅ **Rate limiting** to respect API limits
- ✅ **Error handling** for robust operation
- ✅ **Statistics tracking** for insights

### Web Interface
- ✅ **Interactive timeline editor** with real-time preview
- ✅ **Custom keyword editing** for better search results
- ✅ **Multi-image selection** with thumbnail previews
- ✅ **Session persistence** - selections saved during editing
- ✅ **FCPXML export** for Final Cut Pro integration
- ✅ **Responsive design** works on desktop and mobile

### Command Line
- ✅ **Preview mode** to review results before downloading
- ✅ **Batch processing** for multiple files
- ✅ **Clean JSON output** ready for use
- ✅ **Detailed statistics** and progress reporting

## 🎯 Use Cases

- **Video editing** - Generate FCPXML timelines for Final Cut Pro
- **Presentation creation** - Visual aids synchronized with spoken content
- **Content creation** - Automated image selection for video projects
- **Educational materials** - Visual learning aids with precise timing
- **Social media** - Subtitle-synced image posts and stories
- **Documentary production** - Quick visual research and asset gathering
- **Podcast visualization** - Create visual timelines for audio content

## 🔍 Brave Search API Benefits

- **High-quality results** from comprehensive web index
- **Free tier available** for getting started
- **Fast response times** for real-time applications  
- **No rate limiting hassles** compared to other APIs
- **Clean, structured data** easy to work with

## 🛠️ Development

### Project Architecture
The project follows a modular architecture:
- **`core/`** - Core processing logic (SRT parsing, text splitting, image downloading)
- **`web/`** - Web application components (Flask routes, session management, FCPXML)
- **`utils/`** - Utility functions (time conversion, statistics, file operations)

### Running Tests
```bash
# TODO: Add comprehensive tests
pytest
```

### Code Formatting
```bash
black core/ web/ utils/ *.py
flake8 core/ web/ utils/ *.py
```

## 📝 License

Open source - feel free to use, modify, and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## ❓ Troubleshooting

### Common Issues

**"No subtitle entries found"**
- Check SRT file format
- Ensure file encoding is UTF-8

**"API key invalid"**  
- Verify your Brave Search API key
- Check API subscription status

**"Images not downloading"**
- Check internet connection
- Verify image URLs are accessible
- Check disk space

**"Too many splits"**
- Long subtitles create many splits
- Use shorter subtitle segments
- Adjust splitting algorithm if needed

### Getting Help

- **Web Interface**: Start with `python web_app.py` and open http://localhost:5000
- **Command Line**: Check help with `python main.py --help`
- **Examples**: View examples with `python main.py --examples`
- **API Documentation**: https://api-dashboard.search.brave.com/
- **Project Structure**: All modules are organized in `core/`, `web/`, and `utils/` folders

---

**Made with ❤️ for better subtitle-to-image workflows**