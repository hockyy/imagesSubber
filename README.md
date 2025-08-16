# SRT Image Timeline Generator

A clean, focused Python application that generates image timelines from SRT subtitle files using intelligent text splitting and [Brave Search API](https://api-dashboard.search.brave.com/app/documentation/image-search/get-started).

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
pip install requests nltk Flask
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
3. Upload your SRT file and enter your API key (saved in localStorage)
4. Click search buttons for each timeline split
5. Select multiple images from search results (cached for switching)
6. Export timeline with downloaded images to `./download/{movie_name}/`

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

## 🖥️ GUI Features

The GUI version (`gui_timeline.py`) provides an interactive interface:

- **📁 File Loading**: Browse and load SRT files
- **⚙️ Configuration**: Enter API key and video title
- **📋 Timeline View**: Scrollable list of text splits with timing
- **🔍 Image Search**: Search for images per timeline segment
- **🖼️ Image Selection**: Multi-select images with thumbnails
- **📤 Export**: Save timeline as JSON with selected images

### GUI Workflow:
1. Load SRT file and enter configuration
2. Review generated text splits in timeline
3. Select a timeline item to search for images
4. Choose multiple images from search results
5. Repeat for all timeline segments
6. Export final timeline to JSON

## 🏗️ Project Structure

```
subber/
├── gui_timeline.py        # GUI application (recommended)
├── main.py               # Command line application  
├── srt_parser.py         # SRT file parsing
├── text_splitter.py      # Smart text splitting logic (with NLTK)
├── brave_image_client.py # Brave Search API client
├── timeline_generator.py # Timeline generation (CLI version)
├── requirements.txt      # Dependencies
├── README.md            # This file
└── images/              # Downloaded images (created automatically)
    └── {video_title}/   # Organized by video
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

- ✅ **Smart text splitting** based on duration and content
- ✅ **High-quality images** from Brave Search API
- ✅ **Organized file structure** by video title
- ✅ **Rate limiting** to respect API limits
- ✅ **Error handling** for robust operation
- ✅ **Statistics tracking** for insights
- ✅ **Preview mode** to review results
- ✅ **Clean JSON output** ready for use

## 🎯 Use Cases

- **Video editing** - Sync images with subtitle timing
- **Presentation creation** - Visual aids for spoken content
- **Content creation** - Automated image selection
- **Educational materials** - Visual learning aids
- **Social media** - Subtitle-synced image posts

## 🔍 Brave Search API Benefits

- **High-quality results** from comprehensive web index
- **Free tier available** for getting started
- **Fast response times** for real-time applications  
- **No rate limiting hassles** compared to other APIs
- **Clean, structured data** easy to work with

## 🛠️ Development

### Running Tests
```bash
# TODO: Add tests
pytest
```

### Code Formatting
```bash
black *.py
flake8 *.py
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

- Check command line help: `python main.py --help`
- View examples: `python main.py --examples`
- Review Brave API docs: https://api-dashboard.search.brave.com/

---

**Made with ❤️ for better subtitle-to-image workflows**