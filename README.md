# Video Retrieval Scripts

A collection of tools for video downloading and subtitle extraction, designed for research and data collection purposes.

## Overview

This repository contains a suite of Python scripts for batch video downloading from multiple platforms (YouTube, Bilibili, RTHK) and subtitle processing. The tools are designed to support video retrieval research and multimedia content analysis.

## Scripts

### 1. youtube_excel_downloader.py

An Excel-based batch video downloader that reads video URLs from a spreadsheet and downloads them sequentially.

**Features:**
- Excel input support (.xlsx format)
- Multi-platform support (YouTube, Bilibili, RTHK, youtu.be)
- Automatic video splitting for long content (>30 minutes)
- 360p video quality optimization
- Subtitle extraction and download
- Numbered output files (001, 002, 003...)

**Usage:**
```bash
python3 youtube_excel_downloader.py
```

### 2. youtube_batch_downloader.py

A keyword-based search and download tool for collecting video content by topic.

**Features:**
- Keyword-based video search
- Hong Kong district search term support
- Political content filtering
- Batch download with rate limiting
- Configurable output directory

**Usage:**
```bash
python3 youtube_batch_downloader.py
```

### 3. vtt_to_txt.py

A utility for converting WebVTT subtitle files to plain text format.

**Features:**
- Batch conversion of multiple VTT files
- Automatic encoding detection (UTF-8, GBK, GB2312, Latin-1)
- Removal of VTT metadata and timestamps
- Preservation of subtitle text content

**Usage:**
```bash
python3 vtt_to_txt.py
```

## Requirements

### Common Dependencies
- Python 3.6 or higher
- openpyxl (for Excel reading)
- yt-dlp (for video downloading)
- ffmpeg (for video processing)

### Platform-Specific
- Deno JavaScript runtime (for YouTube challenge solving)
- YouTube account cookies (for restricted content access)

## Installation

```bash
# Install Python dependencies
pip install openpyxl yt-dlp

# Install ffmpeg (macOS)
brew install ffmpeg

# Install Deno (for YouTube JS challenges)
curl -fsSL https://deno.land/x/install/install.sh | sh
```

## Configuration

### youtube_excel_downloader.py

The script reads from `Tour-related Video Info.xlsx` in the following format:
- Column G: Video URLs
- Expected output: `/Volumes/T7 Shield/纪录片collection_1.9`

### youtube_batch_downloader.py

Edit the following variables in the script:
- `SEARCH_TERMS`: List of search keywords
- `OUTPUT_DIR`: Output directory path
- `DOWNLOAD_LIMIT`: Maximum videos to download

## Technical Notes

### Video Splitting

Videos exceeding 30 minutes are automatically split into 10-minute segments using ffmpeg. Output format:
- `XXX_01.mp4` (first 10 minutes)
- `XXX_02.mp4` (next 10 minutes)
- etc.

### Subtitle Formats

- Supported: VTT (WebVTT)
- Auto-generated subtitles are included by default
- Official subtitles are prioritized when available

### Bilibili Download

Bilibili downloads use specific format codes for quality selection:
- 360p: `30016` or `100046` depending on video

## License

MIT License

## Author

Video Retrieval Project
