# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a blog draft generator that uses OpenAI or Anthropic (Claude) APIs to create blog content from attached reference materials (files/folders). It supports both CLI and GUI interfaces and is designed for Korean language content (with English support).

## Running the Application

### GUI Mode
```bash
python -m src.gui
# or
python run_gui.py
```

### CLI Mode
```bash
# OpenAI example
python -m src.main \
  --provider openai \
  --purpose "B2B marketing blog: data-driven, practical tips" \
  --input-dir data/refs \
  notes/*.md \
  --out output/blog_draft.md

# Claude example
python -m src.main \
  --provider anthropic \
  -p "Tutorial for beginners: friendly tone" \
  -d references \
  README.md \
  -o output/draft.md

# or simple
python run_cli.py --provider openai -p "purpose" README.md
```

### CLI Options
- `--provider` (required): `openai` or `anthropic`
- `--model`: Model name (optional, defaults from env or hardcoded)
- `--purpose`/`-p`: Purpose/target/tone instructions
- `--input-dir`/`-d`: Directory to scan recursively
- `files`: Space-separated file paths or glob patterns
- `--out`/`-o`: Output file path (default: `output/blog_draft.md`)
- `--lang`: Output language (default: `ko`)
- `--max-tokens`: Max tokens (default: 1600)
- `--temperature`: Temperature (default: 0.7)
- `--debug`: Print environment diagnostics

## Development Setup

### Dependencies
```bash
pip install -r requirements.txt
```

Requirements:
- Python 3.10+
- `requests>=2.31.0`
- `python-dotenv>=1.0.1`

### Environment Configuration

Copy `.env.example` to `.env` and configure:

**OpenAI:**
- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (optional, for custom endpoints)
- `OPENAI_ORG_ID` (optional, for multi-org accounts)
- `OPENAI_PROJECT` (optional, for project-specific quotas)

**Anthropic:**
- `ANTHROPIC_API_KEY` (required)
- `ANTHROPIC_MODEL` (optional, default: `claude-sonnet-4-5`)
- `ANTHROPIC_BASE_URL` (optional, for custom endpoints)
- `ANTHROPIC_API_VERSION` (optional, default: `2023-06-01`)

Available models (Claude 4.x uses no `-latest` suffix, auto-updates automatically):
- `claude-sonnet-4-5` (recommended, auto-updates to newest Claude 4.5 snapshot)
- `claude-haiku-4-5` (faster, cheaper, auto-updates)
- `claude-sonnet-4-5-20250929` (pinned version for stability)
- `claude-3-7-sonnet-latest` (Claude 3.7, uses `-latest` suffix)
- `claude-3-5-sonnet-20241022` (legacy 3.5 version)

The `.env` file is loaded from both the project root and current working directory (root takes precedence). Use `--debug` flag or GUI "환경 점검" button to verify environment loading.

## Architecture

### Module Structure

```
src/
├── main.py              # CLI entry point, orchestrates the full pipeline
├── gui.py               # Tkinter GUI application
├── prompt_templates.py  # System/user prompt builders for blog generation
├── providers/
│   ├── openai_client.py    # OpenAI API client (chat, ping, quick_chat_test)
│   └── anthropic_client.py # Anthropic API client (chat, ping, quick_chat_test)
└── util/
    ├── file_loader.py   # File collection, text detection, chunking
    └── env_util.py      # .env loading with diagnostics
```

### Key Design Patterns

**Provider Abstraction:**
Both `OpenAIClient` and `AnthropicClient` implement the same interface:
- `chat(model, messages, max_tokens, temperature)` - Main generation method
- `ping()` - Quick connectivity check (GET /models)
- `quick_chat_test()` - Minimal POST test to verify auth and chat endpoint

**Message Format:**
OpenAI-style messages `[{"role": "system"|"user"|"assistant", "content": "..."}]` are used throughout. The Anthropic client converts system messages to the `system` parameter and filters out system roles from messages.

**File Loading Strategy:**
- Files are collected from `--input-dir` (recursive) and explicit file paths/globs
- Only text files are loaded (detected by extension or UTF-8 decode heuristic)
- Each file is chunked to max 12,000 chars, but only the first chunk is used to avoid token overflow
- Attachments are formatted as `[자료 N] path\n```\ncontent\n```\n\n`

**Dual Entry Points:**
The codebase supports both `python -m src.main` and `python src/main.py` via try/except ImportError blocks that handle relative vs absolute imports.

### Prompt Architecture

Prompts are built in three layers:
1. **System Prompt** (`build_system_prompt`): Sets the role as "professional blog editor and SEO consultant"
2. **Attachments Block** (`format_attachments`): Formats loaded files with truncation markers
3. **User Prompt** (`build_user_prompt`): Combines purpose, requirements, output template, and attachments

Output follows a structured template with:
- Title and one-line summary
- Sectioned content with H2/H3 headers
- Conclusion with 3-5 bullets and CTA
- SEO metadata (description, keywords, slug)

### Error Handling Strategy

**Network Errors:**
Both clients implement comprehensive timeout and connection handling:
- Connect timeout: 15s (chat), 10s (ping/test)
- Read timeout: 120s (chat), 20-30s (ping/test)
- Errors are wrapped with actionable Korean messages about proxy/firewall/base_url

**Environment Diagnostics:**
The `env_util.load_env()` function returns a diagnostic dict with:
- `cwd`, `root`: Working directory and project root
- `loaded_env_files`: List of loaded .env file paths
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: Masked key values
- `OPENAI_BASE_URL`, `ANTHROPIC_BASE_URL`: Base URLs

Use `--debug` flag or GUI buttons to expose these diagnostics.

## Testing and Debugging

### Running Tests

**Simple API Test:**
```bash
python test_simple.py
```
Tests Anthropic client initialization and basic API calls with a simple message and blog generation.

**GUI Function Test:**
```bash
python test_gui_direct.py
```
Tests the `run()` function from `main.py` with log callbacks (simulates GUI behavior without actually launching Tkinter).

### GUI Diagnostic Buttons
- **환경 점검**: Prints environment loading diagnostics to log
- **연결 테스트**: Calls provider's `ping()` method to check connectivity
- **짧은 생성 테스트**: Calls `quick_chat_test()` to verify POST auth and response

### CLI Debug Mode
```bash
python -m src.main --provider openai -p "test" README.md --debug
```
Prints: provider, model, language, CWD, root, loaded .env files, masked API keys, base URLs.

### Common Issues

**ImportError with relative imports:**
Always use `python -m src.main` or `python run_cli.py`, not `python src/main.py` directly from wrong directory.

**API calls hang indefinitely:**
Check firewall/proxy settings. Set `HTTPS_PROXY` if behind corporate proxy. Use GUI "연결 테스트" for quick diagnostics.

**HTTP 429 quota errors (OpenAI):**
Set `OPENAI_ORG_ID` and `OPENAI_PROJECT` to use correct quota. Switch to `--provider anthropic` as alternative.

## Code Style Notes

- The codebase is bilingual: code/comments in English, user-facing messages/logs in Korean
- Type hints are used throughout (Python 3.10+ style with `str | None`)
- Error messages are descriptive and actionable in Korean
- GUI uses threading to avoid blocking the UI during API calls
- File paths use `os.path` for cross-platform compatibility
