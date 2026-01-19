#!/usr/bin/env python3
"""
VTT to TXT Converter

This script extracts plain text from WebVTT subtitle files (.vtt) and saves
the content as plain text files (.txt).

Author: Video Retrieval Project
License: MIT
"""

import os
from pathlib import Path


def vtt_to_text(vtt_path: str) -> str:
    """
    Extract plain text from a VTT subtitle file.

    Args:
        vtt_path: Path to the input VTT file.

    Returns:
        A string containing the extracted text content.
    """
    # Attempt multiple encodings to handle different character sets
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']
    content = None

    for encoding in encodings:
        try:
            with open(vtt_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print(f"  Warning: Unable to read {vtt_path}")
        return ""

    lines = content.splitlines()

    text_lines = []
    for line in lines:
        line = line.strip()
        # Skip VTT header and timestamp lines
        if not line or line == 'WEBVTT' or '-->' in line:
            continue
        # Skip lines containing only digits (cue identifiers)
        if line.isdigit():
            continue
        text_lines.append(line)

    return '\n'.join(text_lines)


def convert_all_vtt(directory: str):
    """
    Convert all VTT files in a directory to TXT format.

    Args:
        directory: Path to the directory containing VTT files.
    """
    dir_path = Path(directory)
    vtt_files = list(dir_path.glob('*.vtt'))

    if not vtt_files:
        print(f"No VTT files found in {directory}")
        return

    print(f"Found {len(vtt_files)} VTT files. Starting conversion...")

    for vtt_file in vtt_files:
        txt_file = vtt_file.with_suffix('.txt')
        text = vtt_to_text(str(vtt_file))

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"  {vtt_file.name} -> {txt_file.name}")

    print(f"\nConversion complete. {len(vtt_files)} files processed.")


if __name__ == '__main__':
    convert_all_vtt('/Volumes/T7 Shield/纪录片collection_1.9')
