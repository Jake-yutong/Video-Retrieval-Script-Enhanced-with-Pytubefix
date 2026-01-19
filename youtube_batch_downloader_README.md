# YouTube 批量下载工具优化总结

## 📊 优化前后对比

### 原始方案：pytubefix

```
输入链接 → YouTube() → streams.get_highest_resolution() → download()
```

| 功能 | 状态 |
|------|------|
| 支持单个视频 | ✅ |
| 关键词搜索 | ❌ |
| 批量下载 | ❌ |
| 下载记录 | ❌ |

---

### 优化方案：yt-dlp + youtube_batch_downloader

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 输入关键词   │ ──▶ │  yt-dlp搜索  │ ──▶ │ 获取视频列表 │
└─────────────┘     └─────────────┘     └─────────────┘
                                            │
                                            ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 生成Excel   │ ◀── │ 生成CSV记录 │ ◀── │  批量下载   │
└─────────────┘     └─────────────┘     └─────────────┘
```

| 功能 | 状态 |
|------|------|
| 关键词搜索 | ✅ |
| 批量下载 | ✅ |
| 可选数量 | ✅ |
| CSV记录 | ✅ |
| Excel记录 | ✅ |
| 命令行参数 | ✅ |

---

## 🔧 关键代码改动

### 1. 新增：搜索功能

```python
def search_videos(self, keyword: str, max_results: int) -> list:
    """
    使用yt-dlp搜索视频，返回视频信息列表
    """
    search_url = f"ytsearch{max_results}:{keyword}"
    cmd = ['yt-dlp', '--dump-json', '--flat-playlist', search_url]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    videos = []
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            video_info = json.loads(line)
            videos.append({
                'id': video_info.get('id', ''),
                'title': video_info.get('title', ''),
                'url': f"https://www.youtube.com/watch?v={video_info.get('id', '')}",
                'duration': video_info.get('duration', 0),
                'uploader': video_info.get('uploader', ''),
            })
    return videos
```

### 2. 新增：批量下载循环

```python
for i, video in enumerate(videos[:max_downloads], 1):
    print(f"\n[{i}/{min(len(videos), max_downloads)}]", "="*50)
    self.download_video(video)
    self.downloaded_info.append(video.copy())
```

### 3. 新增：记录生成功能

```python
# 保存CSV
csv_path = self.output_dir / f"{base_name}.csv"
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    fieldnames = ['title', 'url', 'duration', 'uploader', 'status', 'downloaded_at']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(self.downloaded_info)

# 保存Excel (使用openpyxl)
wb = Workbook()
ws = wb.active
ws.title = "下载记录"
ws.append(headers)
for video in self.downloaded_info:
    ws.append([video.get('title', ''), video.get('url', ''), ...])
wb.save(excel_path)
```

### 4. 新增：命令行参数支持

```python
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='YouTube 批量搜索下载工具')
    parser.add_argument('keyword', nargs='?', help='搜索关键词')
    parser.add_argument('--max', type=int, default=10, help='最大下载数量 (默认: 10)')
    return parser.parse_args()
```

### 5. 优化：下载质量控制

```python
# 改为360p以加快下载速度
'-f', 'best[height<=360]',  # 最大360p (快速)
```

---

## 📁 文件结构

```
/Users/liyutong/
├── youtube_batch_downloader.py      # 主脚本
├── youtube_batch_downloader_README.md  # 本文档
└── pytubefix-main/                  # 原始pytubefix库
```

---

## 🚀 使用方法

```bash
# 基本用法
python3 youtube_batch_downloader.py "Hong Kong travel"

# 指定下载数量
python3 youtube_batch_downloader.py "Hong Kong travel" --max 50

# 搜索纪录片
python3 youtube_batch_downloader.py "Hong Kong documentary" --max 100
```

---

## 📍 输出目录

```
/Volumes/T7 Shield/HK:Hong Kong Documentary:HK tourism/
├── video_title_1.mp4
├── video_title_2.mp4
├── ...
├── download_log_with_links_20251230_164248.csv
└── download_log_with_links_20251230_164248.xlsx
```

---

## 📦 依赖安装

```bash
# 安装yt-dlp
python3 -m pip install yt-dlp

# 安装openpyxl (Excel支持)
python3 -m pip install openpyxl
```

---

## ✅ 下载结果

| 项目 | 数值 |
|------|------|
| 视频数量 | 99 个 |
| 总大小 | 8.1 GB |
| 匹配链接 | 69 个 |
| 记录文件 | CSV + Excel |

---

*生成时间：2025-12-30*
