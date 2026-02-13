#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能代码收集工具
提供一键批量导入、智能片段提取、自动结构图生成等功能
"""

import os
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import re

# 尝试导入 code_cleaner 模块
try:
    from code_cleaner import clean_content_deeply, remove_comments, extract_code_skeleton, is_junk_filename
    HAS_CODE_CLEANER = True
except ImportError:
    HAS_CODE_CLEANER = False

# Windows 编码修复
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class CodeCollector:
    """智能代码收集器"""

    def __init__(self, project_path: str, config: Dict = None):
        """初始化收集器"""
        self.project_path = Path(project_path).resolve()
        self.config = config or {}
        self.collected_files = []
        self.structure_tree = {}
        self.existing_md_data = None  # 用于存储已有的 Markdown 解析结果
        # 代码清洗选项
        self.clean_mode = self.config.get('clean_mode', 'none')  # none, comments, skeleton
        self.remove_junk = self.config.get('remove_junk', True)  # 是否移除垃圾文件

    def batch_import(self, file_paths: List[str]) -> Dict:
        """
        一键批量导入多个文件

        参数:
            file_paths: 文件路径列表（相对或绝对路径）

        返回:
            {
                "files": [{"path": "...", "content": "...", "language": "...", "lines": 100}, ...],
                "structure": "树形结构字符串",
                "stats": {"total_files": 10, "total_lines": 1000, "languages": {...}},
                "skipped_files": [{"path": "...", "reason": "..."}, ...]
            }
        """
        result = {
            "files": [],
            "structure": "",
            "stats": {"total_files": 0, "total_lines": 0, "languages": {}},
            "skipped_files": []
        }

        collected_paths = []
        max_size_kb = self.config.get('max_file_size_kb', 500)

        for file_path in file_paths:
            abs_path = self._resolve_path(file_path)
            if not abs_path.exists() or not abs_path.is_file():
                continue

            # 检查文件大小
            file_size_kb = abs_path.stat().st_size / 1024
            if file_size_kb > max_size_kb:
                result["skipped_files"].append({
                    "path": str(file_path),
                    "reason": f"文件过大 ({file_size_kb:.1f} KB > {max_size_kb} KB)",
                    "size_kb": file_size_kb,
                    "lines": self._count_lines(abs_path)
                })
                continue

            # 读取文件内容
            content, encoding = self._read_file_safely(abs_path)
            if content is None:
                result["skipped_files"].append({
                    "path": str(file_path),
                    "reason": "编码错误，无法读取"
                })
                continue

            # 获取相对路径
            try:
                rel_path = abs_path.relative_to(self.project_path)
            except ValueError:
                rel_path = abs_path

            # 垃圾文件过滤
            if self.remove_junk and HAS_CODE_CLEANER:
                if is_junk_filename(str(rel_path)):
                    result["skipped_files"].append({
                        "path": str(file_path),
                        "reason": "垃圾文件（自动过滤）"
                    })
                    continue

            # 代码清洗
            if HAS_CODE_CLEANER and self.clean_mode != 'none':
                ext = abs_path.suffix.lower()
                if self.clean_mode == 'comments':
                    content = remove_comments(content, ext)
                elif self.clean_mode == 'skeleton':
                    content = extract_code_skeleton(content, ext)

            # 语言检测
            language = self._detect_language(abs_path)
            lines = len(content.splitlines())

            result["files"].append({
                "path": str(rel_path),
                "content": content,
                "language": language,
                "lines": lines,
                "size_kb": abs_path.stat().st_size / 1024
            })

            collected_paths.append(rel_path)

            # 更新统计
            result["stats"]["total_lines"] += lines
            result["stats"]["languages"][language] = result["stats"]["languages"].get(language, 0) + 1

        result["stats"]["total_files"] = len(result["files"])

        # 生成目录结构
        result["structure"] = self._generate_tree_structure(collected_paths)

        return result

    def extract_snippets(self, file_path: str, ranges: List[Dict]) -> Dict:
        """
        智能片段提取（支持行号范围和函数名）

        参数:
            file_path: 文件路径
            ranges: 提取范围列表
                [
                    {"type": "lines", "start": 10, "end": 50},
                    {"type": "function", "name": "calculate_total"},
                    {"type": "class", "name": "UserModel"}
                ]

        返回:
            {
                "file_path": "...",
                "snippets": [
                    {"type": "lines", "range": "10-50", "content": "...", "lines": 41},
                    {"type": "function", "name": "calculate_total", "content": "...", "lines": 15}
                ],
                "total_lines": 56
            }
        """
        abs_path = self._resolve_path(file_path)
        if not abs_path.exists():
            return {"error": f"文件不存在: {file_path}"}

        content, _ = self._read_file_safely(abs_path)
        if content is None:
            return {"error": f"无法读取文件: {file_path}"}

        lines = content.splitlines()
        result = {
            "file_path": str(file_path),
            "snippets": [],
            "total_lines": 0
        }

        for range_spec in ranges:
            snippet = None

            if range_spec["type"] == "lines":
                # 按行号提取
                start = range_spec.get("start", 1) - 1  # 转换为 0-based
                end = range_spec.get("end", len(lines))
                snippet_lines = lines[start:end]

                snippet = {
                    "type": "lines",
                    "range": f"{start + 1}-{end}",
                    "content": "\n".join(snippet_lines),
                    "lines": len(snippet_lines)
                }

            elif range_spec["type"] in ["function", "class", "method"]:
                # 按函数/类名提取
                name = range_spec.get("name")
                snippet_content, snippet_lines = self._extract_by_name(
                    content,
                    name,
                    range_spec["type"],
                    abs_path.suffix
                )

                if snippet_content:
                    snippet = {
                        "type": range_spec["type"],
                        "name": name,
                        "content": snippet_content,
                        "lines": snippet_lines
                    }

            if snippet:
                result["snippets"].append(snippet)
                result["total_lines"] += snippet["lines"]

        # 添加统计信息（用于合并模式兼容性）
        language = self._detect_language(abs_path)
        result["stats"] = {
            "total_files": 1,
            "total_lines": result["total_lines"],
            "languages": {language: 1}
        }

        # 将 snippets 转换为合并模式兼容的格式
        result["snippets"] = [{
            "file_path": result["file_path"],
            "snippets": result["snippets"]
        }]

        return result

    def parse_existing_markdown(self, md_path: str) -> Dict:
        """
        解析已有的 Markdown 文件，提取结构化数据

        返回:
            {
                "header": "文件头部内容",
                "files": {
                    "core": [{"path": "...", "content": "...", "language": "..."}],
                    "other": [{"path": "...", "content": "...", "language": "..."}]
                },
                "snippets": [{"file_path": "...", "snippets": [...]}],
                "structure": "目录结构字符串",
                "stats": {...},
                "skipped_files": [...]
            }
        """
        if not os.path.exists(md_path):
            return None

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            "header": "",
            "files": {"core": [], "other": []},
            "snippets": [],
            "structure": "",
            "stats": {},
            "skipped_files": []
        }

        # 提取文件头部（从开始到第一个 ## 标题）
        header_match = re.search(r'^(.*?)(?=^## )', content, re.MULTILINE | re.DOTALL)
        if header_match:
            result["header"] = header_match.group(1)

        # 提取目录结构
        structure_match = re.search(r'## 📁 目录结构\s*\n\s*```(?:text)?\n(.*?)\n```', content, re.DOTALL)
        if structure_match:
            result["structure"] = structure_match.group(1)

        # 提取核心文件
        core_section = re.search(r'## 🎯 核心文件\s*\n(.*?)(?=^## |$)', content, re.MULTILINE | re.DOTALL)
        if core_section:
            result["files"]["core"] = self._parse_file_sections(core_section.group(1))

        # 提取普通文件
        other_section = re.search(r'## 📄 代码文件\s*\n(.*?)(?=^## |$)', content, re.MULTILINE | re.DOTALL)
        if other_section:
            result["files"]["other"] = self._parse_file_sections(other_section.group(1))

        # 提取代码片段
        snippet_sections = re.finditer(r'## 📄 代码片段: (.+?)\n(.*?)(?=^## |$)', content, re.MULTILINE | re.DOTALL)
        for match in snippet_sections:
            file_path = match.group(1)
            snippet_content = match.group(2)
            snippets = self._parse_snippet_sections(snippet_content)
            result["snippets"].append({"file_path": file_path, "snippets": snippets})

        # 提取跳过的文件
        skipped_section = re.search(r'## ⚠️ 跳过的文件\s*\n(.*?)(?=^## |$)', content, re.MULTILINE | re.DOTALL)
        if skipped_section:
            result["skipped_files"] = self._parse_skipped_files(skipped_section.group(1))

        return result

    def _parse_file_sections(self, section_content: str) -> List[Dict]:
        """解析文件段落"""
        files = []
        file_matches = re.finditer(r'### File: (.+?)\n\s*```(\w+)?\n(.*?)\n```', section_content, re.DOTALL)
        for match in file_matches:
            files.append({
                "path": match.group(1),
                "language": match.group(2) or "text",
                "content": match.group(3)
            })
        return files

    def _parse_snippet_sections(self, section_content: str) -> List[Dict]:
        """解析代码片段段落"""
        snippets = []

        # 匹配函数/类片段
        func_matches = re.finditer(r'### (Function|Class|Method): (.+?)\n\s*```.*?\n(.*?)\n```', section_content, re.DOTALL)
        for match in func_matches:
            snippets.append({
                "type": match.group(1).lower(),
                "name": match.group(2),
                "content": match.group(3)
            })

        # 匹配行范围片段
        line_matches = re.finditer(r'### 行 (\d+-\d+)\n\s*```.*?\n(.*?)\n```', section_content, re.DOTALL)
        for match in line_matches:
            snippets.append({
                "type": "lines",
                "range": match.group(1),
                "content": match.group(2)
            })

        return snippets

    def _parse_skipped_files(self, section_content: str) -> List[Dict]:
        """解析跳过的文件列表"""
        skipped = []
        file_matches = re.finditer(r'### (.+?)\n(.*?)(?=### |$)', section_content, re.DOTALL)
        for match in file_matches:
            file_path = match.group(1)
            details = match.group(2)

            reason_match = re.search(r'\*\*原因\*\*：(.+)', details)
            size_match = re.search(r'\*\*文件大小\*\*：(.+)', details)

            skipped.append({
                "path": file_path,
                "reason": reason_match.group(1) if reason_match else "未知原因",
                "size_kb": float(size_match.group(1).split()[0]) if size_match else None
            })

        return skipped

    def merge_markdown_data(self, existing: Dict, new_data: Dict) -> Dict:
        """
        合并新旧数据

        参数:
            existing: 已有的解析数据
            new_data: 新的数据（来自 batch_import 或 extract_snippets）

        返回:
            合并后的数据结构
        """
        if not existing:
            return new_data

        merged = {
            "header": existing["header"],  # 保留原有头部
            "files": existing["files"].copy() if "files" in existing else {"core": [], "other": []},
            "snippets": existing["snippets"].copy() if "snippets" in existing else [],
            "structure": existing["structure"],
            "stats": existing["stats"].copy() if "stats" in existing else {},
            "skipped_files": existing["skipped_files"].copy() if "skipped_files" in existing else []
        }

        # 合并文件列表（去重）
        if "files" in new_data:
            existing_paths = {f["path"] for f in merged["files"]["core"] + merged["files"]["other"]}

            for file_info in new_data["files"]:
                if file_info["path"] not in existing_paths:
                    if self._is_core_file(file_info["path"]):
                        merged["files"]["core"].append(file_info)
                    else:
                        merged["files"]["other"].append(file_info)

        # 合并代码片段
        if "snippets" in new_data:
            # 查找是否已有该文件的片段
            existing_snippet_files = {s["file_path"]: i for i, s in enumerate(merged["snippets"])}

            for snippet_data in new_data["snippets"]:
                file_path = snippet_data["file_path"]
                if file_path in existing_snippet_files:
                    # 合并到已有文件的片段列表（去重）
                    idx = existing_snippet_files[file_path]
                    existing_snippet_names = {
                        s.get("name") or s.get("range")
                        for s in merged["snippets"][idx]["snippets"]
                    }

                    for snippet in snippet_data["snippets"]:
                        snippet_id = snippet.get("name") or snippet.get("range")
                        if snippet_id not in existing_snippet_names:
                            merged["snippets"][idx]["snippets"].append(snippet)
                else:
                    # 添加新文件的片段
                    merged["snippets"].append(snippet_data)

        # 合并目录结构
        if "structure" in new_data and new_data["structure"]:
            merged["structure"] = self._merge_tree_structures(
                existing["structure"],
                new_data["structure"]
            )

        # 更新跳过的文件列表（移除已成功提取的）
        if "snippets" in new_data:
            extracted_files = {s["file_path"] for s in new_data.get("snippets", [])}
            merged["skipped_files"] = [
                s for s in merged["skipped_files"]
                if s["path"] not in extracted_files
            ]

        # 添加新跳过的文件（去重）
        if "skipped_files" in new_data:
            existing_skipped_paths = {s["path"] for s in merged["skipped_files"]}
            for skipped in new_data["skipped_files"]:
                if skipped["path"] not in existing_skipped_paths:
                    merged["skipped_files"].append(skipped)

        # 更新统计信息
        if "stats" in new_data:
            merged["stats"]["total_files"] = (
                len(merged["files"]["core"]) +
                len(merged["files"]["other"]) +
                len(merged["snippets"])
            )
            merged["stats"]["total_lines"] = existing["stats"].get("total_lines", 0) + new_data["stats"].get("total_lines", 0)

            # 合并语言统计
            merged["stats"]["languages"] = existing["stats"].get("languages", {}).copy()
            for lang, count in new_data["stats"].get("languages", {}).items():
                merged["stats"]["languages"][lang] = merged["stats"]["languages"].get(lang, 0) + count

        return merged

    def _merge_tree_structures(self, existing: str, new: str) -> str:
        """合并两个树形目录结构"""
        if not existing:
            return new
        if not new:
            return existing

        # 简化处理：将两个树合并（实际场景中可以更智能地合并）
        # 提取所有文件路径，重新生成树
        def extract_paths(tree_str: str) -> Set[str]:
            paths = set()
            for line in tree_str.split('\n'):
                # 移除树形字符，提取路径
                clean_line = re.sub(r'[├└│─\s]+', '', line).strip('/')
                if clean_line:
                    paths.add(clean_line)
            return paths

        existing_paths = extract_paths(existing)
        new_paths = extract_paths(new)
        all_paths = existing_paths | new_paths

        # 这里简化处理，返回原有结构（实际可以重新生成完整树）
        return existing

    def generate_markdown(self, data: Dict, user_intent: str = "", append_mode: bool = False, existing_md_path: str = None) -> str:
        """
        生成 Markdown 文档

        参数:
            data: batch_import 或 extract_snippets 返回的数据
            user_intent: 用户意图描述
            append_mode: 是否为追加模式（智能合并到对应区域）
            existing_md_path: 已有 Markdown 文件路径（追加模式需要）

        返回:
            完整的 Markdown 字符串
        """
        # 追加模式：解析已有文件并合并数据
        if append_mode and existing_md_path:
            existing_data = self.parse_existing_markdown(existing_md_path)
            if existing_data:
                # 合并数据
                data = self.merge_markdown_data(existing_data, data)

        md_parts = []

        # 标题和元信息
        project_name = self.project_path.name
        md_parts.append(f"# Project: {project_name}\n")

        # 元信息
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if append_mode and existing_md_path:
            md_parts.append(f"**最后更新**: {update_time}\n")
        else:
            md_parts.append(f"**生成时间**: {update_time}\n")

        if user_intent:
            md_parts.append(f"**收集目的**: {user_intent}\n")

        # 项目类型（如果有）
        if "detected_project_type" in self.config:
            md_parts.append(f"**项目类型**: {self.config.get('project_type_name', '未知')}\n")

        md_parts.append("\n---\n\n")

        # 目录结构
        if "structure" in data and data["structure"]:
            md_parts.append("## 📁 目录结构\n\n")
            md_parts.append("```text\n")
            md_parts.append(data["structure"])
            md_parts.append("\n```\n\n---\n\n")

        # 文件内容（批量导入模式 - 支持合并后的数据）
        if "files" in data and isinstance(data["files"], dict):
            # 处理合并后的数据结构
            core_files = data["files"].get("core", [])
            other_files = data["files"].get("other", [])

            if core_files:
                md_parts.append("## 🎯 核心文件\n\n")
                for file_info in core_files:
                    md_parts.append(self._format_file_section(file_info))

            if other_files:
                md_parts.append("## 📄 代码文件\n\n")
                for file_info in other_files:
                    md_parts.append(self._format_file_section(file_info))
        elif "files" in data and isinstance(data["files"], list):
            # 处理原始数据结构（首次生成）
            core_files = []
            other_files = []

            for file_info in data["files"]:
                if self._is_core_file(file_info["path"]):
                    core_files.append(file_info)
                else:
                    other_files.append(file_info)

            if core_files:
                md_parts.append("## 🎯 核心文件\n\n")
                for file_info in core_files:
                    md_parts.append(self._format_file_section(file_info))

            if other_files:
                md_parts.append("## 📄 代码文件\n\n")
                for file_info in other_files:
                    md_parts.append(self._format_file_section(file_info))

        # 代码片段（片段提取模式 - 支持合并后的数据）
        if "snippets" in data:
            if isinstance(data["snippets"], list) and len(data["snippets"]) > 0:
                # 合并后的数据结构
                if isinstance(data["snippets"][0], dict) and "file_path" in data["snippets"][0]:
                    for snippet_group in data["snippets"]:
                        md_parts.append(f"## 📄 代码片段: {snippet_group['file_path']}\n\n")
                        for snippet in snippet_group["snippets"]:
                            md_parts.append(self._format_snippet_section(snippet))
                # 原始数据结构（首次生成）
                else:
                    md_parts.append(f"## 📄 代码片段: {data.get('file_path', '未知')}\n\n")
                    for snippet in data["snippets"]:
                        md_parts.append(self._format_snippet_section(snippet))

        # 统计信息
        if "stats" in data:
            md_parts.append("## 📊 统计信息\n\n")
            stats = data["stats"]
            md_parts.append(f"- 总文件数：{stats['total_files']}\n")
            md_parts.append(f"- 总代码行数：{stats['total_lines']}\n")

            if stats.get("languages"):
                lang_stats = []
                total = sum(stats["languages"].values())
                for lang, count in sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True):
                    pct = (count / total) * 100
                    lang_stats.append(f"{lang} ({pct:.1f}%)")
                md_parts.append(f"- 主要语言：{', '.join(lang_stats)}\n")

        # 跳过的文件（如果有）
        if "skipped_files" in data and data["skipped_files"]:
            md_parts.append("\n---\n\n")
            md_parts.append("## ⚠️ 跳过的文件\n\n")
            md_parts.append("以下文件因体积过大或编码问题未能自动收集，**需要 Agent 手动处理**：\n\n")
            for skipped in data["skipped_files"]:
                md_parts.append(f"### {skipped['path']}\n\n")
                md_parts.append(f"- **原因**：{skipped['reason']}\n")
                if 'size_kb' in skipped:
                    md_parts.append(f"- **文件大小**：{skipped['size_kb']:.1f} KB\n")
                if 'lines' in skipped and skipped['lines']:
                    md_parts.append(f"- **预估行数**：约 {skipped['lines']} 行\n")
                md_parts.append(f"- **建议**：使用片段提取模式 (--mode snippets) 指定函数/类名或行号范围\n\n")

        # 用户意图总结（文末）
        if user_intent:
            md_parts.append("\n---\n\n")
            md_parts.append("## 🎯 收集目的总结\n\n")
            md_parts.append(f"{user_intent}\n\n")
            md_parts.append("**提示**：以上代码已根据此目的收集整理，可直接用于相关分析或开发任务。\n")

        return "".join(md_parts)

    def _resolve_path(self, path: str) -> Path:
        """解析路径（支持相对和绝对路径）"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.project_path / p

    def _read_file_safely(self, path: Path) -> Tuple[Optional[str], Optional[str]]:
        """安全读取文件（尝试多种编码）"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read(), encoding
            except (UnicodeDecodeError, FileNotFoundError):
                continue

        return None, None

    def _count_lines(self, path: Path) -> Optional[int]:
        """快速统计文件行数（不完整读取）"""
        try:
            with open(path, 'rb') as f:
                return sum(1 for _ in f)
        except:
            return None

    def _detect_language(self, path: Path) -> str:
        """检测编程语言"""
        ext = path.suffix.lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'jsx', '.tsx': 'tsx', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.h': 'c', '.hpp': 'cpp',
            '.cs': 'csharp', '.go': 'go', '.rs': 'rust',
            '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
            '.kt': 'kotlin', '.scala': 'scala', '.r': 'r',
            '.m': 'objective-c', '.sql': 'sql', '.sh': 'bash',
            '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json',
            '.xml': 'xml', '.html': 'html', '.css': 'css',
            '.scss': 'scss', '.sass': 'sass', '.md': 'markdown',
            '.vue': 'vue', '.svelte': 'svelte'
        }
        return lang_map.get(ext, 'text')

    def _generate_tree_structure(self, file_paths: List[Path]) -> str:
        """生成树形目录结构"""
        if not file_paths:
            return ""

        # 构建树形结构
        tree = {}
        for path in file_paths:
            parts = path.parts
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # 渲染树形结构
        def render_tree(node: Dict, prefix: str = "", is_last: bool = True) -> List[str]:
            lines = []
            items = sorted(node.items())

            for i, (name, children) in enumerate(items):
                is_last_item = (i == len(items) - 1)

                if prefix == "":
                    lines.append(f"{name}/")
                    lines.extend(render_tree(children, "    ", is_last_item))
                else:
                    connector = "└── " if is_last_item else "├── "
                    is_file = len(children) == 0
                    display_name = name if is_file else f"{name}/"
                    lines.append(f"{prefix}{connector}{display_name}")

                    if children:
                        extension = "    " if is_last_item else "│   "
                        lines.extend(render_tree(children, prefix + extension, is_last_item))

            return lines

        tree_lines = render_tree(tree)
        return "\n".join(tree_lines)

    def _extract_by_name(self, content: str, name: str, element_type: str, file_ext: str, skeleton_mode: bool = False) -> Tuple[Optional[str], int]:
        """根据函数/类名提取代码

        参数:
            content: 文件内容
            name: 函数/类名
            element_type: 类型 (function, class, method)
            file_ext: 文件扩展名
            skeleton_mode: 是否使用骨架模式（仅提取声明，去除实现）
        """
        lines = content.splitlines()

        # 根据文件类型选择正则模式
        if file_ext in ['.py']:
            if element_type == 'function':
                pattern = rf'^\s*def\s+{re.escape(name)}\s*\('
            elif element_type == 'class':
                pattern = rf'^\s*class\s+{re.escape(name)}\s*[\(:]'
            else:
                return None, 0
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.vue']:
            if element_type == 'function':
                # 更精确的函数定义模式，排除函数调用
                pattern = rf'(^\s*function\s+{re.escape(name)}\s*\(|^\s*async\s+function\s+{re.escape(name)}\s*\(|^\s*const\s+{re.escape(name)}\s*=|^\s*let\s+{re.escape(name)}\s*=|^\s*var\s+{re.escape(name)}\s*=)'
            elif element_type == 'class':
                pattern = rf'^\s*class\s+{re.escape(name)}\s*'
            else:
                return None, 0
        elif file_ext in ['.java', '.kt', '.cs']:
            if element_type in ['function', 'method']:
                pattern = rf'\s+{re.escape(name)}\s*\('
            elif element_type == 'class':
                pattern = rf'class\s+{re.escape(name)}\s*'
            else:
                return None, 0
        elif file_ext in ['.go']:
            # Go 语言函数支持
            if element_type in ['function', 'method']:
                pattern = rf'^\s*func\s+(?:\([^)]+\)\s*)?{re.escape(name)}\s*\('
            elif element_type == 'type':
                pattern = rf'^\s*type\s+{re.escape(name)}\s*'
            else:
                return None, 0
        elif file_ext in ['.rs']:
            # Rust 语言函数支持
            if element_type in ['function', 'method']:
                pattern = rf'^\s*(?:pub\s+)?fn\s+{re.escape(name)}\s*'
            elif element_type == 'struct':
                pattern = rf'^\s*(?:pub\s+)?struct\s+{re.escape(name)}\s*'
            elif element_type == 'enum':
                pattern = rf'^\s*(?:pub\s+)?enum\s+{re.escape(name)}\s*'
            else:
                return None, 0
        elif file_ext in ['.cpp', '.cc', '.cxx', '.hpp']:
            # C++ 支持
            if element_type in ['function', 'method']:
                pattern = rf'^\s*(?:template\s*<[^>]*>\s*)?(?:inline\s+)?(?:void|int|string|bool|auto|auto\s+|[\w:]+)\s+{re.escape(name)}\s*\('
            elif element_type == 'class':
                pattern = rf'^\s*class\s+{re.escape(name)}\s*(?::|\{)'
            else:
                return None, 0
        else:
            # 通用模式
            pattern = rf'\b{re.escape(name)}\b'

        # 查找定义行
        start_line = None
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                start_line = i
                break

        if start_line is None:
            return None, 0

        # 根据文件类型选择不同的结束行判断策略
        brace_languages = ['.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.vue',
                          '.java', '.kt', '.cs', '.cpp', '.c', '.cc', '.cxx', '.h', '.hpp',
                          '.go', '.rs']

        if skeleton_mode and file_ext in brace_languages:
            # 骨架模式：使用 code_cleaner 的 hollow_out_function_bodies
            from code_cleaner import hollow_out_function_bodies
            snippet_lines = lines[start_line:]
            full_content = "\n".join(snippet_lines)
            cleaned = hollow_out_function_bodies(full_content)
            return cleaned, len(cleaned.splitlines())
        elif file_ext in brace_languages:
            # 对于大括号语言，使用括号匹配
            end_line = self._find_closing_brace(lines, start_line)
        else:
            # 对于 Python 等缩进语言，使用缩进判断
            end_line = self._find_end_by_indent(lines, start_line)

        snippet_lines = lines[start_line:end_line]
        return "\n".join(snippet_lines), len(snippet_lines)

    def _find_closing_brace(self, lines: List[str], start_line: int) -> int:
        """通过大括号配对找到代码块结束位置（用于 JavaScript/Java/C++ 等）"""
        brace_count = 0
        found_opening = False

        for i in range(start_line, len(lines)):
            line = lines[i]

            # 跳过字符串和注释中的括号（简化处理）
            # 移除单行注释
            if '//' in line:
                code_part = line[:line.index('//')]
            else:
                code_part = line

            # 统计括号
            for char in code_part:
                if char == '{':
                    brace_count += 1
                    found_opening = True
                elif char == '}':
                    brace_count -= 1

                # 找到匹配的闭括号
                if found_opening and brace_count == 0:
                    return i + 1

        # 如果没有找到匹配的括号，返回文件末尾
        return len(lines)

    def _find_end_by_indent(self, lines: List[str], start_line: int) -> int:
        """通过缩进判断代码块结束位置（用于 Python 等）"""
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = start_line + 1

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                continue

            current_indent = len(line) - len(line.lstrip())

            # 如果缩进回到同级或更少，结束
            if current_indent <= base_indent and line.strip():
                end_line = i
                break
        else:
            end_line = len(lines)

        return end_line

    def _is_core_file(self, file_path: str) -> bool:
        """判断是否为核心文件"""
        core_files = self.config.get('core_files', [])
        file_name = Path(file_path).name

        # 检查完整路径或文件名
        return any(
            file_path == core or
            file_name == core or
            file_path.endswith(core)
            for core in core_files
        )

    def _format_file_section(self, file_info: Dict) -> str:
        """格式化文件段落"""
        md = f"### File: {file_info['path']}\n\n"
        md += f"```{file_info['language']}\n"
        md += file_info['content']
        md += "\n```\n\n---\n\n"
        return md

    def _format_snippet_section(self, snippet: Dict) -> str:
        """格式化代码片段段落"""
        if snippet['type'] == 'lines':
            md = f"### 行 {snippet['range']}\n\n"
        else:
            md = f"### {snippet['type'].title()}: {snippet['name']}\n\n"

        md += "```\n"
        md += snippet['content']
        md += "\n```\n\n---\n\n"
        return md


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='智能代码收集工具')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--mode', choices=['batch', 'snippets'], required=True,
                        help='运行模式：batch（批量导入）或 snippets（片段提取）')
    parser.add_argument('--files', nargs='+', help='文件列表（batch 模式）')
    parser.add_argument('--target', help='目标文件（snippets 模式）')
    parser.add_argument('--ranges', help='提取范围 JSON（snippets 模式）')
    parser.add_argument('--intent', help='用户意图描述')
    parser.add_argument('--config', help='配置文件路径（JSON）')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--append', action='store_true',
                        help='追加模式：向现有文件追加内容，而不是覆盖')
    parser.add_argument('--clean', choices=['none', 'comments', 'skeleton'], default='none',
                        help='代码清洗模式：none-不处理, comments-去注释, skeleton-骨架模式')
    parser.add_argument('--no-junk-filter', action='store_true',
                        help='禁用垃圾文件过滤（STM32/Unity等自动生成文件）')

    args = parser.parse_args()

    # 加载配置
    config = {}
    config_path = args.config
    
    if not config_path:
        # 默认尝试从父目录加载 config.json
        default_config = Path(__file__).parent.parent / "config.json"
        if default_config.exists():
            config_path = str(default_config)

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # 创建收集器
    collector = CodeCollector(args.project_path, config)

    # 应用命令行清洗参数
    if args.clean != 'none':
        collector.clean_mode = args.clean
    if args.no_junk_filter:
        collector.remove_junk = False

    # 执行收集
    if args.mode == 'batch':
        if not args.files:
            print("错误：batch 模式需要指定 --files", file=sys.stderr)
            sys.exit(1)

        data = collector.batch_import(args.files)

    elif args.mode == 'snippets':
        if not args.target or not args.ranges:
            print("错误：snippets 模式需要指定 --target 和 --ranges", file=sys.stderr)
            sys.exit(1)

        ranges = json.loads(args.ranges)
        data = collector.extract_snippets(args.target, ranges)

    # 命令行实时反馈：检查跳过的文件
    if 'skipped_files' in data and data['skipped_files']:
        print("\n" + "=" * 60)
        print("[警告] 检测到以下文件未能自动收集：")
        print("=" * 60)
        for skipped in data['skipped_files']:
            print(f"\n文件: {skipped['path']}")
            print(f"原因: {skipped['reason']}")
            if 'size_kb' in skipped:
                print(f"文件大小: {skipped['size_kb']:.1f} KB")
            if 'lines' in skipped and skipped['lines']:
                print(f"预估行数: 约 {skipped['lines']} 行")
            print("建议: 使用 --mode snippets 指定函数/类名或行号范围提取")
        print("=" * 60 + "\n")

    # 生成 Markdown（追加模式时传入已有文件路径）
    markdown = collector.generate_markdown(
        data,
        args.intent or "",
        append_mode=args.append,
        existing_md_path=args.output if args.append else None
    )

    # 输出（追加模式统一使用覆盖写入，因为已经在内存中合并了）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown)

        action = "已合并更新到" if args.append else "已保存到"
        print(f"✅ {action}: {args.output}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
