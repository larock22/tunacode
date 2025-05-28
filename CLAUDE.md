# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TunaCode is an agentic CLI-based AI development tool, providing an open-source alternative to Claude Code, Copilot, and Cursor. It supports multiple LLM providers (Anthropic, OpenAI, Google Gemini, OpenRouter) without vendor lock-in.

## Essential Commands

### Development
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run TunaCode locally
tunacode

# Development commands
make lint         # Run black, isort, flake8
make test         # Run pytest
make coverage     # Run tests with coverage report
make build        # Build distribution package
make clean        # Clean build artifacts
make run          # Run TunaCode from env/bin/tunacode
```

### Running Single Tests
```bash
pytest path/to/test_file.py::TestClass::test_method
pytest -v -s path/to/test_file.py  # Verbose with stdout
```

### Configuration
TunaCode uses `tunacode_config.yml` for TinyAgent integration. The config is searched in order:
1. Package root directory
2. `~/.config/tunacode_config.yml`
3. Current working directory

Key environment variables:
- `OPENAI_API_KEY` - OpenAI API authentication
- `ANTHROPIC_API_KEY` - Anthropic API authentication  
- `GEMINI_API_KEY` - Google Gemini API authentication
- `OPENROUTER_API_KEY` - OpenRouter API authentication
- `OPENAI_BASE_URL` - Override API base URL

## Architecture

### Core Components

1. **StateManager** (`src/tunacode/core/state.py`) - Central state management handling:
   - Session state and message history
   - Agent instances and cost tracking
   - Configuration and environment setup

2. **Agent System**:
   - Primary: TinyAgent-based implementation (`src/tunacode/core/agents/tinyagent_main.py`)
   - Legacy: Pydantic-AI implementation (`src/tunacode/core/agents/main.py`)
   - Implements tool-first approach for all operations
   - Message history management with compaction support

3. **Tool Framework** (`src/tunacode/tools/`):
   - Base classes provide consistent error handling and UI logging
   - TinyAgent tools: `read_file`, `write_file`, `update_file`, `run_command` (in `tinyagent_tools.py`)
   - Pydantic-AI tools in separate files (`read_file.py`, `write_file.py`, etc.)
   - All tools inherit from `BaseTool` or `FileBasedTool`

4. **Setup Coordinator** (`src/tunacode/core/setup/coordinator.py`):
   - Modular initialization system with registered setup steps
   - Handles environment, config, and undo setup

5. **UI Layer** (`src/tunacode/ui/`):
   - Terminal UI using `prompt_toolkit` and `rich`
   - Custom lexers, completers, and keybindings
   - Tool confirmation system with skip options

### Key Design Patterns

- **Tool-First Approach**: Agent prioritizes using tools for all file/command operations
- **Git-Based Undo**: Uses git for reverting changes via `/undo` command
- **Per-Project Guides**: `TUNACODE.md` files for project-specific instructions
- **MCP Support**: Model Context Protocol for extended capabilities
- **Cost Tracking**: Per-message and session-level token/cost tracking

## Code Style

- Line length: 100 characters (configured in black and isort)
- Import sorting: isort with black compatibility
- Type hints encouraged throughout codebase
- Follow conventional commits for version history
- Formatting: `black` with `--line-length 100`
- Import order: `isort` with `line_length=100` and `profile=black`

## Testing Approach

- Tests use pytest (framework in development)
- Mock external services and file operations
- Test tools independently from agent logic
- Verify UI components separately from core logic

## Release Process

1. Update version in `pyproject.toml` and `src/tunacode/constants.py`
2. Follow conventional commits specification
3. Tag with `vX.Y.Z` format
4. Create GitHub release
5. PyPI release automated on main branch merge

## Key Dependencies

- **tiny_agent_os>=0.1.0** - Core agent framework (TinyAgent)
- **prompt_toolkit==3.0.51** - Terminal UI and input handling
- **rich==14.0.0** - Rich terminal output formatting
- **pygments==2.19.1** - Syntax highlighting for code
- **typer==0.12.5** - CLI framework for commands