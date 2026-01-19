#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 批量搜索下载工具 - 纪录片优化版
功能：关键词搜索 → 智能过滤 → 批量下载 → 生成记录
"""

import os
import sys
import csv
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# 尝试导入openpyxl，如果失败则使用csv
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# ============ 过滤配置 ============
# 必须包含的关键词（满足任一即可）
TITLE_MUST_CONTAIN = [
    "Hong Kong", "hong kong",
    "HK", "hk",
    "香港",
    "🇭🇰",
]

# 排除的关键词（包含任一即排除）
TITLE_EXCLUDE_KEYWORDS = [
    "Full review", "full review",
    "Apartment", "apartment",
    "Cage", "cage",
]

# 政治敏感词汇（排除）- 避免地域歧视和政治相关内容
POLITICAL_KEYWORDS = [
    # 抗议/示威相关
    "protest", "demonstration", "riot", "march", "rally",
    "umbrella", "占中", "雨伞",
    # 政治事件
    "politics", "political", "election", "vote",
    # 敏感历史/冲突
    "日軍", "侵港", "占領", "日军", "日本军", "sars",
    # 分离/独立相关
    "independence", "independenc", "autonomy",
    # 其他敏感
    "freedom", "democracy", "human rights abuse",
    # 政治媒体/来源
    "BBC News 中文", "RTHK",
]

# 最小时长（4分钟 = 240秒）
MIN_DURATION_SECONDS = 4 * 60  # 240秒


class YouTubeDocumentaryDownloader:
    def __init__(self, output_dir: str, max_downloads: int = 50, exclude_dir: str = None):
        self.output_dir = Path(output_dir)
        self.max_downloads = max_downloads
        self.downloaded_info = []
        self.filtered_info = []  # 过滤后的视频信息
        self.exclude_titles = set()  # 已下载的视频标题（用于去重）

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载已下载的视频标题用于去重
        if exclude_dir:
            exclude_path = Path(exclude_dir)
            if exclude_path.exists():
                for mp4 in exclude_path.glob("*.mp4"):
                    # 标准化标题用于匹配
                    title = mp4.stem.lower().strip()
                    self.exclude_titles.add(title)
                print(f"   📋 已加载 {len(self.exclude_titles)} 个已下载视频用于去重")

    def _contains_keyword(self, text: str, keywords: list) -> bool:
        """检查文本是否包含任一关键词"""
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    def _is_excluded(self, title: str) -> bool:
        """检查标题是否应该被排除"""
        # 排除包含特定词汇
        if self._contains_keyword(title, TITLE_EXCLUDE_KEYWORDS):
            return True
        # 排除政治敏感内容
        if self._contains_keyword(title, POLITICAL_KEYWORDS):
            return True
        return False

    def _is_valid_title(self, title: str) -> bool:
        """检查标题是否有效（必须包含HK/香港相关词汇）"""
        # 先排除
        if self._is_excluded(title):
            return False
        # 再检查是否包含必需词汇
        if self._contains_keyword(title, TITLE_MUST_CONTAIN):
            return True
        return False

    def _is_duplicate(self, title: str) -> bool:
        """检查是否与已下载的视频重复"""
        normalized_title = title.lower().strip()
        # 检查是否在已下载列表中（模糊匹配）
        for downloaded in self.exclude_titles:
            # 如果有30个以上字符相同，认为是重复
            if len(normalized_title) > 20 and len(downloaded) > 20:
                # 计算相似度
                common = set(normalized_title.split()) & set(downloaded.split())
                if len(common) >= 3:  # 有3个以上相同词
                    return True
        return False

    def _filter_videos(self, videos: list) -> list:
        """
        智能过滤视频：
        1. 排除已下载的视频
        2. 标题包含 HK/香港 相关词汇
        3. 排除特定词汇
        4. 排除政治敏感内容（标题和上传者）
        5. 时长至少10分钟
        """
        filtered = []
        excluded_by_title = 0
        excluded_by_duration = 0
        excluded_by_political = 0
        excluded_by_duplicate = 0
        excluded_by_filter = 0

        for video in videos:
            title = video.get('title', '')
            uploader = video.get('uploader', '')

            # 1. 检查是否重复
            if self._is_duplicate(title):
                excluded_by_duplicate += 1
                continue

            # 2. 检查政治敏感内容（标题或上传者）
            if self._contains_keyword(title, POLITICAL_KEYWORDS) or self._contains_keyword(uploader, POLITICAL_KEYWORDS):
                excluded_by_political += 1
                continue

            # 3. 检查标题是否包含必需词汇
            if not self._is_valid_title(title):
                excluded_by_title += 1
                continue

            # 4. 检查时长
            duration = video.get('duration', 0) or 0
            if duration < MIN_DURATION_SECONDS:
                excluded_by_duration += 1
                continue

            # 通过所有过滤条件
            filtered.append(video)

        print(f"\n📊 过滤统计:")
        print(f"   原始数量: {len(videos)}")
        print(f"   有效数量: {len(filtered)}")
        print(f"   已重复: {excluded_by_duplicate}")
        print(f"   标题不符: {excluded_by_title}")
        print(f"   过滤词汇: {excluded_by_filter}")
        print(f"   时长不足: {excluded_by_duration}")
        print(f"   政治敏感: {excluded_by_political}")

        return filtered

    def search_videos(self, keyword: str, max_results: int = None) -> list:
        """
        使用yt-dlp搜索视频，返回视频信息列表
        搜索更广泛的关键词以获取更多结果
        """
        if max_results is None:
            max_results = self.max_downloads

        print(f"\n🔍 正在搜索: {keyword}")
        print(f"   搜索数量: {max_results}")

        # 扩展搜索：使用多个相关关键词，覆盖不同上传时间
        search_terms = [
            # 纪录片类
            "Hong Kong documentary",
            "Hong Kong history documentary",
            "香港纪录片",
            "Hong Kong culture documentary",
            "Hong Kong food documentary",
            "Hong Kong travel documentary",
            "Hong Kong city documentary",
            "Hong Kong lifestyle documentary",
            "Hong Kong urban exploration",
            "Hong Kong heritage documentary",
            # 旅游/Vlog类
            "Hong Kong travel vlog",
            "Hong Kong tourism guide",
            "Hong Kong travel guide",
            "Hong Kong vlog",
            "Hong Kong trip",
            "visit Hong Kong",
            "Hong Kong vacation",
            "Hong Kong 4K travel",
            "Hong Kong scenic",
            # 香港各区 - 中西区
            "Kennedy Town Hong Kong travel",
            "Shek Tong Tsui Hong Kong",
            "Sai Ying Pun Hong Kong vlog",
            "Sheung Wan Hong Kong travel",
            "Central Hong Kong travel",
            "Admiralty Hong Kong documentary",
            "Mid-Levels Hong Kong",
            "Peak Tram Hong Kong travel",
            # 湾仔区
            "Wan Chai Hong Kong travel",
            "Causeway Bay Hong Kong vlog",
            "Happy Valley Hong Kong",
            "Tai Hang Hong Kong",
            "Jardine's Lookout Hong Kong",
            # 东区
            "Tin Hau Hong Kong",
            "North Point Hong Kong travel",
            "Quarry Bay Hong Kong",
            "Sai Wan Ho Hong Kong",
            "Shau Kei Wan Hong Kong",
            "Chai Wan Hong Kong travel",
            # 南区
            "Aberdeen Hong Kong travel",
            "Ap Lei Chau Hong Kong",
            "Repulse Bay Hong Kong travel",
            "Stanley Hong Kong documentary",
            "Shek O Hong Kong",
            "Wong Chuk Hang Hong Kong",
            # 油尖旺
            "Tsim Sha Tsui Hong Kong travel",
            "Yau Ma Tei Hong Kong",
            "Mong Kok Hong Kong vlog",
            "West Kowloon Hong Kong",
            # 深水埗
            "Mei Foo Hong Kong",
            "Lai Chi Kok Hong Kong",
            "Cheung Sha Wan Hong Kong",
            "Sham Shui Po Hong Kong",
            "Shek Kip Mei Hong Kong",
            # 九龙城
            "Hung Hom Hong Kong travel",
            "To Kwa Wan Hong Kong",
            "Kai Tak Hong Kong",
            "Ho Man Tin Hong Kong",
            "Kowloon Tong Hong Kong",
            # 黄大仙
            "San Po Kong Hong Kong",
            "Wong Tai Sin Hong Kong",
            "Diamond Hill Hong Kong",
            "Tsz Wan Shan Hong Kong",
            # 观塘
            "Kowloon Bay Hong Kong",
            "Ngau Tau Kok Hong Kong",
            "Kwun Tong Hong Kong travel",
            "Lam Tin Hong Kong",
            "Yau Tong Hong Kong",
            "Lei Yue Mun Hong Kong",
            # 葵青
            "Kwai Chung Hong Kong travel",
            "Tsing Yi Hong Kong",
            # 荃湾
            "Tsuen Wan Hong Kong travel",
            "Ma Wan Hong Kong",
            "Ting Kau Hong Kong",
            # 屯门
            "Tuen Mun Hong Kong travel",
            "Lam Tei Hong Kong",
            # 元朗
            "Yuen Long Hong Kong travel",
            "Tin Shui Wai Hong Kong",
            "Lok Ma Chau Hong Kong",
            "Kam Tin Hong Kong",
            # 北区
            "Fanling Hong Kong travel",
            "Sheung Shui Hong Kong",
            "Sha Tau Kok Hong Kong",
            # 大埔
            "Tai Po Hong Kong travel",
            "Tai Mei Tuk Hong Kong",
            # 沙田
            "Tai Wai Hong Kong",
            "Sha Tin Hong Kong travel",
            "Ma On Shan Hong Kong",
            "Wu Kai Sha Hong Kong",
            # 西贡
            "Clear Water Bay Hong Kong",
            "Sai Kung Hong Kong travel",
            "Tseung Kwan O Hong Kong",
            "Hang Hau Hong Kong",
            # 离岛
            "Cheung Chau Hong Kong travel",
            "Lamma Island Hong Kong vlog",
            "Lantau Island Hong Kong travel",
            "Tung Chung Hong Kong",
            # 综合搜索
            "Hong Kong neighborhoods travel",
            "Hong Kong local guide vlog",
            "Hong Kong off the beaten path",
            "Hong Kong hidden gems travel",
        ]

        all_videos = []
        seen_ids = set()

        for term in search_terms:
            if len(all_videos) >= max_results * 3:  # 获取更多以供筛选
                break

            search_url = f"ytsearch100:{term}"

            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                '--flat-playlist',
                search_url
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180
                )

                if result.returncode != 0:
                    continue

                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            video_info = json.loads(line)
                            video_id = video_info.get('id', '')

                            # 去重
                            if video_id in seen_ids:
                                continue
                            seen_ids.add(video_id)

                            # 提取上传时间
                            upload_date = video_info.get('upload_date', '')
                            if upload_date:
                                # 格式: YYYYMMDD
                                try:
                                    upload_time = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
                                except:
                                    upload_time = ''
                            else:
                                upload_time = ''

                            # 提取观看次数
                            view_count = video_info.get('view_count', 0) or 0

                            all_videos.append({
                                'id': video_id,
                                'title': video_info.get('title', ''),
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'duration': video_info.get('duration', 0),
                                'uploader': video_info.get('uploader', ''),
                                'upload_time': upload_time,
                                'views': view_count,
                            })
                        except json.JSONDecodeError:
                            continue

            except subprocess.TimeoutExpired:
                print(f"   ⚠️ 搜索超时: {term}")
                continue
            except Exception as e:
                print(f"   ⚠️ 搜索出错: {term} - {e}")
                continue

        print(f"   搜索完成，获取 {len(all_videos)} 个候选视频")

        # 智能过滤
        filtered_videos = self._filter_videos(all_videos)

        # 按上传时间排序，确保覆盖不同时期的视频
        filtered_videos.sort(key=lambda x: x.get('upload_time', ''))

        # 限制数量
        final_videos = filtered_videos[:max_results]

        print(f"   最终筛选出 {len(final_videos)} 个视频")
        return final_videos

    def download_video(self, video_info: dict) -> bool:
        """
        下载单个视频
        """
        url = video_info['url']
        title = video_info['title']

        # 清理文件名中的非法字符
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        safe_title = safe_title[:80]

        print(f"\n📥 正在下载: {safe_title}")
        print(f"   链接: {url}")

        cmd = [
            'yt-dlp',
            '-f', 'best[height<=360]',  # 360p快速模式
            '-o', str(self.output_dir / f"%(title)s.%(ext)s"),
            '--no-playlist',
            '--no-check-certificate',
            '--merge-output-format', 'mp4',
            '--add-metadata',
            url
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900  # 15分钟超时
            )

            if result.returncode == 0:
                print(f"   ✅ 下载完成")
                video_info['downloaded_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                video_info['status'] = '成功'
                return True
            else:
                error_msg = result.stderr[-200:] if result.stderr else '未知错误'
                print(f"   ❌ 下载失败")
                video_info['status'] = f'失败'
                return False

        except subprocess.TimeoutExpired:
            print("   ❌ 下载超时")
            video_info['status'] = '超时'
            return False
        except Exception as e:
            print(f"   ❌ 下载出错: {e}")
            video_info['status'] = f'错误'
            return False

    def download_all(self, keyword: str, max_downloads: int = None):
        """
        搜索并批量下载视频
        """
        if max_downloads is None:
            max_downloads = self.max_downloads

        # 搜索视频
        videos = self.search_videos(keyword, max_downloads)

        if not videos:
            print("\n❌ 未找到符合条件的视频")
            return

        # 保存过滤后的视频信息（不含下载状态）
        self.filtered_info = [v.copy() for v in videos]

        # 下载每个视频
        print(f"\n🚀 开始下载 ({len(videos)} 个)...")
        print(f"📁 保存目录: {self.output_dir}")

        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}]", "="*50)
            self.download_video(video)
            self.downloaded_info.append(video.copy())

        # 保存记录
        self.save_records(keyword)

    def save_records(self, keyword: str):
        """
        保存下载记录到Excel和CSV文件
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"doc_collection_{keyword[:15]}_{timestamp}"

        # CSV字段：title, upload_time, uploader, views, duration, web_link
        csv_headers = ['title', 'upload_time', 'uploader', 'views', 'video_length', 'web_link']
        csv_field_map = {
            'title': 'title',
            'upload_time': 'upload_time',
            'uploader': 'uploader',
            'views': 'views',
            'video_length': 'duration',
            'web_link': 'url',
        }

        # 保存CSV - 优先使用 filtered_info（未下载的也记录）
        csv_path = self.output_dir / f"{base_name}.csv"
        data_to_save = self.filtered_info if self.filtered_info else self.downloaded_info

        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()

            for video in data_to_save:
                row = {}
                for csv_key, video_key in csv_field_map.items():
                    value = video.get(video_key, '')

                    # 格式化时长
                    if csv_key == 'video_length':
                        duration = value or 0
                        if duration:
                            minutes = int(duration) // 60
                            seconds = int(duration) % 60
                            value = f"{minutes}:{seconds:02d}"
                        else:
                            value = ""

                    # 格式化观看次数
                    if csv_key == 'views':
                        value = f"{value:,}" if value else ""

                    row[csv_key] = value

                writer.writerow(row)

        print(f"\n📄 CSV记录已保存: {csv_path}")

        # 保存Excel (如果可用)
        if EXCEL_AVAILABLE:
            excel_path = self.output_dir / f"{base_name}.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "纪录片合集"

            # 表头
            headers = ['标题', '上传时间', '上传者', '观看次数', '时长', '链接']
            ws.append(headers)

            # 数据
            for video in data_to_save:
                duration = video.get('duration', 0) or 0
                if duration:
                    duration_str = f"{duration // 60}:{duration % 60:02d}"
                else:
                    duration_str = ""

                views = video.get('views', 0) or 0
                views_str = f"{views:,}"

                row = [
                    video.get('title', ''),
                    video.get('upload_time', ''),
                    video.get('uploader', ''),
                    views_str,
                    duration_str,
                    video.get('url', ''),
                ]
                ws.append(row)

            # 调整列宽
            ws.column_dimensions['A'].width = 60
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 25
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 50

            # 表头样式
            header_font = Font(bold=True)
            for cell in ws[1]:
                cell.font = header_font

            wb.save(excel_path)
            print(f"📊 Excel记录已保存: {excel_path}")

        # 打印摘要
        success_count = sum(1 for v in self.downloaded_info if v.get('status') == '成功')
        print(f"\n📊 下载摘要:")
        print(f"   成功: {success_count}/{len(self.downloaded_info)}")
        print(f"   记录: {len(data_to_save)} 个视频")
        print(f"   保存目录: {self.output_dir}")


def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(
        description='YouTube 纪录片批量搜索下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
过滤规则:
  - 标题必须包含: Hong Kong / HK / 香港 / 🇭🇰
  - 排除: Full review / Apartment / Cage
  - 排除政治敏感内容
  - 时长至少20分钟

示例:
  python3 youtube_batch_downloader.py "Hong Kong documentary"
  python3 youtube_batch_downloader.py "Hong Kong documentary" --max 50
        """
    )
    parser.add_argument('keyword', nargs='?', help='搜索关键词')
    parser.add_argument('--max', type=int, default=50, help='最大下载数量 (默认: 50)')
    return parser.parse_args()


def main():
    """主函数"""
    print("="*60)
    print("   YouTube 纪录片批量下载工具")
    print("   过滤: HK/香港 | 排除: review/Apartment/Cage")
    print("   时长: >= 4分钟 | 各区搜索 | 去重")
    print("="*60)

    # 配置参数
    OUTPUT_DIR = "/Volumes/T7 Shield/纪录片collection 1.6"
    EXCLUDE_DIR = "/Volumes/T7 Shield/HK:Hong Kong Documentary:HK tourism"  # 已下载视频目录，用于去重
    DEFAULT_MAX = 100

    # 获取命令行参数
    args = parse_args()

    # 如果没有提供关键词，交互式输入
    if not args.keyword:
        try:
            keyword = input("\n🔤 请输入搜索关键词: ").strip()
        except EOFError:
            print("\n❌ 请在命令行运行并提供关键词，例如:")
            print('   python3 youtube_batch_downloader.py "Hong Kong documentary"')
            sys.exit(1)
    else:
        keyword = args.keyword

    max_downloads = args.max if args.max else DEFAULT_MAX

    # 创建下载器并执行（传入exclude_dir用于去重）
    downloader = YouTubeDocumentaryDownloader(OUTPUT_DIR, max_downloads, exclude_dir=EXCLUDE_DIR)
    downloader.download_all(keyword, max_downloads)

    print("\n" + "="*60)
    print("   任务完成！")
    print("="*60)


if __name__ == "__main__":
    main()
