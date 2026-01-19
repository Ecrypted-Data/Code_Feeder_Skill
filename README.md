# Code Feeder Skill 🚀

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Claude](https://img.shields.io/badge/Skill-Claude%20Code-purple)

[🇬🇧 English Documentation](README.md) | [🇨🇳 中文文档](README_ZH.md)

> **Intelligent Code Collector** — Automatically collects project code, intelligently records user intent, and generates AI-friendly context documentation with one click.

> 🙏 **Acknowledgements**: This project is inspired by [AI_CodeFeeder_by_py](https://github.com/ChaoPhone/AI_CodeFeeder_by_py), special thanks to the original author for the inspiration.

**Code Feeder** is a Skill built specifically for **Claude Code**, upgrading your CLI Agent into an intelligent context collection expert.

It aims to solve the pain point of collaborating with AI: **How to efficiently provide project context to LLMs?** It automates code collection, generates directory structures, and records your intent, allowing you to "feed" the generated Markdown directly to WEB-based AI, **without repeating background explanations**.

---

## 🤔 Why Code Feeder?

Even if you already use Cursor, GitHub Copilot, or Claude CLI, this tool is an essential supplement for **deep development**:

1.  **🧠 Pure Code Insight**:
    IDE and CLI AIs are often burdened with many Tools, MCP protocols, and environmental context. Excessive interference can sometimes distract the model from the code itself. In contrast, providing clean code context to Web-based AI often yields deeper logical analysis and architectural advice.

2.  **🚀 Official Web Performance**:
    Experience shows that official Web models (like ChatGPT Plus, Claude.ai, Gemini Web) often possess **stronger reasoning capabilities** and hidden chain-of-thought optimizations. They frequently outperform API-based backend models when dealing with complex refactoring or difficult bugs.

3.  **💰 Significantly Reduced Token Costs**:
    Instead of consuming expensive API quotas for repeated trial and error in the CLI, generate precise context documentation with one click and leverage the (often flat-rate) Web interface for unlimited deep exploration.

---

## ✨ Core Features

- **🎯 Intent Recording**: Records your purpose (e.g., "refactor auth module") during collection, automatically including it in the generated docs so external AIs understand immediately.
- **🚀 Two Collection Modes**:
  - **Batch Import**: Ideal for small projects, packs all relevant files at once.
  - **Smart Snippet Extraction**: Ideal for large projects, supports precise extraction by **function name**, **class name**, or **line numbers**, no manual copy-pasting required.
- **🌲 Structure Visualization**: Intelligently generates project directory trees to clearly show code organization.
- **🤖 Project Type Detection**: Automatically identifies 12+ project types like React, Django, Rust, Unity, applying optimal filtering rules.
- **📊 Auto-Statistics**: Provides stats on line counts, language distribution, and core file identification.

---

## 🛠 Supported Project Types

System automatically detects types and optimizes collection strategy (ignoring irrelevant files, prioritizing core ones):

| Frontend | Backend/System | Others |
| :--- | :--- | :--- |
| <img src="https://skillicons.dev/icons?i=react" width="20"/> React / Next.js | <img src="https://skillicons.dev/icons?i=django" width="20"/> Django | <img src="https://skillicons.dev/icons?i=unity" width="20"/> Unity |
| <img src="https://skillicons.dev/icons?i=vue" width="20"/> Vue / Nuxt | <img src="https://skillicons.dev/icons?i=fastapi" width="20"/> FastAPI | <img src="https://skillicons.dev/icons?i=c" width="20"/> STM32 Embedded |
| <img src="https://skillicons.dev/icons?i=nodejs" width="20"/> Node.js | <img src="https://skillicons.dev/icons?i=rust" width="20"/> Rust / Go | 🐍 Python (Generic) |

*And generic support for Java, C#, C++, PHP, etc.*

---

## 🚀 Installation

### Global Installation (Recommended)

Make Code Feeder available in all projects:

1.  Go to Claude Skills directory:
    *   **macOS/Linux**: `cd ~/.claude/skills`
    *   **Windows (PowerShell)**: `cd $env:USERPROFILE\.claude\skills`
    *   *Create the directory if it doesn't exist.*

2.  Clone the repository:
    ```bash
    git clone https://github.com/Ecrypted-Data/Code_Feeder_Skill.git code-feeder
    ```

3.  **Verify Installation**:
    Restart Claude Code, then ask:
    > "What skills do you have available?"

    If you see `code-feeder` in the list, installation is successful!

### Project-level Installation

Use only in the current project:
Create a `.claude/skills` folder in your project root and clone the code into it.

---

## 💡 Usage

### In Claude Code

Talk directly to the Agent:

> "Use code-feeder to collect project code for me, I want to refactor the user login module."

The Agent will automatically:
1. Ask for your specific intent.
2. Detect project type.
3. Execute collection and generate `markdown` documentation.

### Manual CLI Usage

You can also run the Python script directly:

#### 1. Batch Mode (Batch)
Suitable for collecting entire modules or small projects.

```bash
python scripts/code_collector.py /path/to/project \
  --mode batch \
  --files src/main.py src/utils.py \
  --intent "Analyze main logic flow" \
  --output context.md
```

#### 2. Snippets Mode (Snippets)
Suitable for extracting specific functions or classes from large files.

```bash
python scripts/code_collector.py /path/to/project \
  --mode snippets \
  --target src/auth_service.py \
  --ranges "[
    {\"type\": \"function\", \"name\": \"login\"},
    {\"type\": \"class\", \"name\": \"UserSession\"}
  ]" \
  --intent "Check login security" \
  --output context.md
```

---

## 🔍 Features Detail

### Smart Snippet Extraction
Say goodbye to scrolling through thousands of lines to find a function. Just tell the tool the function name, and it automatically locates and extracts the complete code block (including indentation).

Supported languages:
- Python, JavaScript, TypeScript
- Java, Kotlin, C#
- C, C++, Go, Rust
- And more...

### Intent-Driven Documentation
The generated Markdown is not just a code dump, but a **Task Manual**.

**Output Example:**
```markdown
# Project: MyApp
**Date**: 2026-01-18
**Purpose**: Refactor user auth module, analyze security

## 📁 Directory Structure
...

## 📄 Code Content
...

## 🎯 Intent Summary
Need to refactor the user authentication module, hoping AI will analyze security and performance bottlenecks in existing code.
**Tip**: The code above has been collected based on this purpose and can be used directly for analysis or development tasks.
```
*Send this doc to AI, and it will immediately understand: "Oh, you need me to analyze auth security and performance," without extra explanation.*

---

## ⚙️ Configuration

Config file is at `config.json`. Usually no modification needed.

**Default Ignores:**
`.git`, `node_modules`, `venv`, `__pycache__`, `dist`, `build`, etc.

**Custom Config:**
You can modify `config.json` to:
- Add custom ignore directories.
- Set max file size limit (default 500KB).
- Define "core files" list.

---

## 📂 File Structure

```text
code-feeder/
├── skill.md             # Claude Skill core instructions & metadata
├── README.md            # English documentation
├── README_ZH.md         # Chinese documentation
├── config.json          # Default configuration
├── project-types.json   # Project type detection rules
└── scripts/             # Tool scripts directory
    ├── code_collector.py      # Core collection logic
    └── detect_project.py      # Project type detection tool
```

---

## 🤝 Contribution

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Submit Pull Request

## 📄 License

This project is open source under the MIT License - see [LICENSE](LICENSE) file for details.
