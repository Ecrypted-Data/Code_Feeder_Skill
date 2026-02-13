#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码清洗模块
提供去注释、骨架模式、垃圾文件过滤等功能
"""

import re
from typing import Optional


def hollow_out_function_bodies(content: str) -> str:
    """
    【骨架模式核心】保留结构，掏空实现
    基于大括号计数 ({ count })

    参数:
        content: 原始代码内容

    返回:
        掏空函数体后的代码（保留结构）
    """
    output = []
    i = 0
    length = len(content)
    brace_depth = 0
    in_string = False
    in_char = False

    while i < length:
        char = content[i]

        # 1. 简单的字符串跳过逻辑
        if char == '"' and (i == 0 or content[i - 1] != '\\'):
            in_string = not in_string
            output.append(char)
            i += 1
            continue
        if char == "'" and (i == 0 or content[i - 1] != '\\'):
            in_char = not in_char
            output.append(char)
            i += 1
            continue

        if in_string or in_char:
            output.append(char)
            i += 1
            continue

        # 2. 大括号逻辑
        if char == '{':
            if brace_depth == 0:
                output.append('{')
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth == 0:
                output.append('}')
        else:
            if brace_depth == 0:
                output.append(char)
            elif brace_depth == 1 and output and output[-1] == '{':
                output.append(' /* ... */ ')  # 简化占位符

        i += 1

    return "".join(output)


def remove_license_header(content: str) -> str:
    """移除常见的顶部版权注释"""
    match = re.match(r'^\s*/\*[\s\S]*?\*/', content)
    if match:
        header = match.group(0)
        # 简单判定：包含 license/copyright 等关键词
        if any(k in header.lower() for k in ['copyright', 'license', 'author', 'file']):
            return content[len(header):].lstrip()
    return content


def clean_content_deeply(content: str, ext: str, aggressive_mode: bool = False) -> str:
    """
    深度清洗流水线

    参数:
        content: 原始代码内容
        ext: 文件扩展名 (如 '.py', '.cpp')
        aggressive_mode: True=骨架模式, False=Gap模式(仅去注释)

    返回:
        清洗后的代码内容
    """
    ext = ext.lower()

    # 1. 根据后缀决定清洗逻辑
    if ext == '.py':
        # 移除 Python import
        content = re.sub(r'^\s*(import|from)\s+.*$', '', content, flags=re.MULTILINE)
        # 移除 Python 单行注释
        content = re.sub(r'#.*', '', content)
        # 移除 Python 多行注释 (''' 或 """) - 简单处理，不考虑字符串内的情况
        content = re.sub(r'\'\'\'[\s\S]*?\'\'\'', '', content)
        content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', content)

    elif ext in ['.c', '.cpp', '.h', '.hpp']:
        # 移除 C/C++ 引用
        content = re.sub(r'^\s*#\s*(include|pragma|import).*$', '', content, flags=re.MULTILINE)
        # 移除 C/C++ 单行注释
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        # 移除 C/C++ 块注释
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        # 移除 JavaScript/TypeScript 注释
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    elif ext in ['.java', '.kt', '.scala']:
        # 移除 Java/Kotlin 注释
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    elif ext in ['.go', '.rs']:
        # 移除 Go/Rust 注释
        content = re.sub(r'//.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    # 2. 骨架模式 (仅对支持大括号的语言有效)
    if aggressive_mode and ext in ['.c', '.cpp', '.h', '.hpp', '.js', '.ts', '.jsx', '.tsx', '.java', '.kt', '.go', '.rs']:
        content = hollow_out_function_bodies(content)

    # 3. 格式整理 (去多余空行)
    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def is_junk_filename(filename: str, extra_patterns: Optional[list] = None) -> bool:
    """
    文件名级过滤
    检测常见的垃圾文件（如 STM32 自动生成文件）

    参数:
        filename: 文件名或路径
        extra_patterns: 额外的过滤模式列表

    返回:
        True 表示应该过滤掉
    """
    # 基础垃圾文件名正则
    base_patterns = [
        r'stm32.*?xx',       # STM32 自动生成
        r'system_',          # 系统文件
        r'stm32f4xx_hal_conf',  # STM32 HAL 配置
        r'FreeRTOSConfig',   # FreeRTOS 配置
    ]

    # 添加额外模式
    if extra_patterns:
        base_patterns.extend(extra_patterns)

    for pattern in base_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True

    return False


def extract_code_skeleton(content: str, ext: str) -> str:
    """
    提取代码骨架 - 保留函数/类声明，去除实现

    参数:
        content: 原始代码
        ext: 文件扩展名

    返回:
        骨架代码
    """
    ext = ext.lower()

    if ext == '.py':
        # Python: 保留 def/class 声明，去除函数体
        return _extract_python_skeleton(content)
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        # JavaScript/TypeScript
        return _extract_js_skeleton(content)
    elif ext in ['.java', '.kt']:
        return _extract_java_skeleton(content)
    else:
        # 其他语言使用通用的骨架模式
        return hollow_out_function_bodies(content)


def _extract_python_skeleton(content: str) -> str:
    """提取 Python 代码骨架"""
    lines = content.splitlines()
    result = []
    in_function = False
    base_indent = 0

    for line in lines:
        stripped = line.strip()

        # 检测函数/类定义
        if stripped.startswith('def ') or stripped.startswith('class '):
            result.append(line)
            in_function = False
            continue

        # 检测函数体开始
        if in_function:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and stripped:
                in_function = False
                result.append(line)
        else:
            result.append(line)

        # 设置函数体缩进基准
        if 'def ' in stripped and '(' in stripped:
            in_function = True
            base_indent = len(line) - len(line.lstrip())

    return '\n'.join(result)


def _extract_js_skeleton(content: str) -> str:
    """提取 JavaScript/TypeScript 代码骨架"""
    return hollow_out_function_bodies(content)


def _extract_java_skeleton(content: str) -> str:
    """提取 Java/Kotlin 代码骨架"""
    return hollow_out_function_bodies(content)


def remove_comments(content: str, ext: str) -> str:
    """
    仅移除注释，保留代码结构

    参数:
        content: 原始代码
        ext: 文件扩展名

    返回:
        去除注释后的代码
    """
    return clean_content_deeply(content, ext, aggressive_mode=False)
