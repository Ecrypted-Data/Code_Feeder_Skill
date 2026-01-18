# Code Feeder Skill 🚀

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Claude](https://img.shields.io/badge/Skill-Claude%20Code-purple)

> **智能代码收集器** — 自动化收集项目代码，智能记录用户意图，一键生成 AI 友好的上下文文档。

Code Feeder 是一个Claude Code skill，旨在解决与 AI 协作时的痛点：**如何高效地将项目上下文提供给 LLM?** 它能自动化收集代码、生成目录结构、并记录你的意图，让你能直接将生成的 Markdown "喂"给WEB端的AI，**无需重复解释背景**。

---

## 🤔 为什么需要 Code Feeder？

即使你已经拥有 Cursor、GitHub Copilot 或 Claude CLI，此工具依然是**深度开发**的必备补充：

1.  **🧠 更纯粹的代码洞察力**：
    IDE 和 CLI 中的 AI 往往负载了大量工具（Tools）、MCP 协议和环境上下文。过多的干扰有时会导致模型对代码本身的**注意力分散**。相比之下，将纯净的代码上下文提供给 Web 端 AI，往往能获得更深刻的逻辑分析和架构建议。

2.  **🚀 官方 Web 端的性能优势**：
    实践表明，官方 Web 端（如 ChatGPT Plus, Claude.ai, DeepSeek Web）的模型往往拥有**更强的推理能力**和隐藏的思维链优化，在处理复杂重构或疑难 Bug 时，表现常优于通过 API 调用的后端模型。

3.  **💰 显著降低 Token 开销**：
    与其在 CLI 中消耗昂贵的 API 额度进行反复试错和长对话，不如一键生成精准的上下文文档，利用 Web 端（通常是包月制）的算力进行无限制的深度探讨。

---

## ✨ 核心特性

- **🎯 用户意图自动记录**：在收集代码时记录你的目的（如"重构认证模块"），生成文档时自动包含意图说明，外部 AI 一看即懂。
- **🚀 两种收集模式**：
  - **批量导入**：适合小型项目，一键打包所有相关文件。
  - **智能片段提取**：适合大型项目，支持按**函数名**、**类名**或**行号**精准提取，无需手动复制粘贴。
- **🌲 自动结构可视化**：智能生成项目目录树，清晰展示代码组织结构。
- **🤖 项目类型检测**：自动识别 React, Django, Rust, Unity 等 12+ 种项目类型，智能应用最佳过滤规则。
- **📊 自动统计分析**：提供代码行数、语言占比、核心文件识别等统计数据。

---

## 🛠 支持的项目类型

系统会自动检测以下类型并优化采集策略（忽略无关文件，优先核心文件）：

| 前端 | 后端/系统 | 其他 |
| :--- | :--- | :--- |
| <img src="https://skillicons.dev/icons?i=react" width="20"/> React / Next.js | <img src="https://skillicons.dev/icons?i=django" width="20"/> Django | <img src="https://skillicons.dev/icons?i=unity" width="20"/> Unity |
| <img src="https://skillicons.dev/icons?i=vue" width="20"/> Vue / Nuxt | <img src="https://skillicons.dev/icons?i=fastapi" width="20"/> FastAPI | <img src="https://skillicons.dev/icons?i=c" width="20"/> STM32 Embedded |
| <img src="https://skillicons.dev/icons?i=nodejs" width="20"/> Node.js | <img src="https://skillicons.dev/icons?i=rust" width="20"/> Rust / Go | 🐍 Python (Generic) |

*以及 Java, C#, C++, PHP 等通用支持。*

---

## 🚀 安装说明

### 方法 1：作为 Claude Code Skill (推荐)

如果你使用 Claude Code，可以将此仓库作为 Skill 集成：

```bash
# 假设你的 skills 目录在 ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/YourUsername/code-feeder.git
```

### 方法 2：独立使用

你也可以直接作为 Python 工具使用：

```bash
git clone https://github.com/YourUsername/code-feeder.git
cd code-feeder
# 无需安装额外依赖，仅需 Python 3.8+ 标准库
```

---

## 💡 使用方法

### 在 Claude Code 中

直接与 Agent 对话：

> "使用 code-feeder 帮我收集项目代码，我想重构用户登录模块。"

Agent 会自动：
1. 询问你的具体意图。
2. 检测项目类型。
3. 执行收集并生成 `markdown` 文档。

### 命令行手动使用

你也可以直接运行 Python 脚本：

#### 1. 批量导入模式 (Batch)
适合收集整个模块或小项目。

```bash
python scripts/code_collector.py /path/to/project \
  --mode batch \
  --files src/main.py src/utils.py \
  --intent "分析主逻辑流程" \
  --output context.md
```

#### 2. 片段提取模式 (Snippets)
适合从大文件中提取特定函数或类。

```bash
python scripts/code_collector.py /path/to/project \
  --mode snippets \
  --target src/auth_service.py \
  --ranges "[
    {\"type\": \"function\", \"name\": \"login\"},
    {\"type\": \"class\", \"name\": \"UserSession\"}
  ]" \
  --intent "检查登录安全性" \
  --output context.md
```

---

## 🔍 功能详解

### 智能片段提取
告别手动滚动几千行代码寻找函数。只需告诉工具函数名，它会自动定位并提取完整代码块（包括缩进）。

支持语言：
- Python, JavaScript, TypeScript
- Java, Kotlin, C#
- C, C++, Go, Rust
- 更多...

### 意图驱动的文档生成
生成的 Markdown 文档不仅是代码堆砌，更是**任务说明书**。

**输出示例：**
```markdown
# Project: MyApp
**生成时间**: 2026-01-18
**收集目的**: 重构用户认证模块，分析安全性

## 📁 目录结构
...

## 📄 代码内容
...

## 🎯 收集目的总结
需要重构用户认证模块，希望 AI 分析现有代码的安全性和性能瓶颈。
**提示**：以上代码已根据此目的收集整理，可直接用于相关分析或开发任务。
```
*将此文档复制给 ChatGPT，它会立即理解："哦，你需要我分析认证模块的安全性和性能"，无需你再费口舌。*

---

## ⚙️ 配置指南

配置文件位于 `config.json`。通常无需修改，系统会自动适配。

**默认忽略：**
`.git`, `node_modules`, `venv`, `__pycache__`, `dist`, `build` 等。

**自定义配置：**
你可以修改 `config.json` 来：
- 添加自定义忽略目录。
- 设置最大文件大小限制（默认 500KB）。
- 定义项目的"核心文件"列表。

---

## 📂 文件结构

```text
code-feeder/
├── SKILL.md             # Claude Skill 核心指令与元数据
├── README.md            # 项目说明文档
├── config.json          # 默认配置文件
├── project-types.json   # 项目类型检测规则
└── scripts/             # 工具脚本目录
    ├── code_collector.py      # 代码收集核心逻辑
    └── detect_project.py      # 项目类型检测工具
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 鸣谢

本项目受 [AI_CodeFeeder_by_py](https://github.com/ChaoPhone/AI_CodeFeeder_by_py) 启发而开发，特此感谢。