# VTT to TXT Converter

A command-line utility for extracting plain text from WebVTT subtitle files.

## Overview

This script processes WebVTT (.vtt) subtitle files and converts them into plain text (.txt) format. It is designed for video retrieval and text mining applications where subtitle content needs to be extracted for further analysis.

## Features

- Batch conversion of multiple VTT files in a specified directory
- Automatic encoding detection (UTF-8, GBK, GB2312, Latin-1)
- Removal of VTT metadata, timestamps, and cue identifiers
- Preservation of subtitle text content in readable format
- Command-line interface for easy integration into automated workflows

## Requirements

- Python 3.6 or higher
- Standard library only (no external dependencies)

## Usage

```bash
python3 vtt_to_txt.py
```

By default, the script processes VTT files in the following directory:
`/Volumes/T7 Shield/纪录片collection_1.9`

To process a different directory, modify the `directory` parameter in the `__main__` section:

```python
if __name__ == '__main__':
    convert_all_vtt('/path/to/your/vtt/files')
```

## Input Format

The script accepts WebVTT subtitle files with the following structure:

```
WEBVTT

1
00:00:01.000 --> 00:00:04.000
First line of subtitle text
Second line of subtitle text

2
00:00:04.500 --> 00:00:08.000
Another subtitle entry
```

## Output Format

The output is a plain text file containing only the subtitle content:

```
First line of subtitle text
Second line of subtitle text
Another subtitle entry
```

## Technical Details

### Encoding Handling

The script attempts to read files using multiple character encodings in the following order:
1. UTF-8
2. UTF-8 with BOM
3. GBK (Simplified Chinese)
4. GB2312 (Simplified Chinese)
5. Latin-1 (Western European)

This approach ensures compatibility with subtitle files from various sources and regions.

### Filtering Rules

The following elements are excluded from the output:
- `WEBVTT` header
- Timestamp lines (containing `-->`)
- Cue numeric identifiers
- Empty lines
- Position/style annotations

## License

MIT License

## Author

Video Retrieval Project
