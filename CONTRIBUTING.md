# Contributing to TunaCode

Thank you for your interest in contributing to TunaCode! We welcome contributions from the community and are excited to see what you'll bring to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully
- Prioritize the project's best interests

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tunacode
   cd tunacode
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/alchemiststudiosDOTai/tunacode
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Make (optional but recommended)

### Environment Setup

1. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   # Or using make:
   make install
   ```

3. **Verify installation**:
   ```bash
   tunacode --version
   ```

### IDE Configuration

We recommend using VSCode with the following extensions:
- Python
- Black Formatter
- isort
- Pylance

Example `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "editor.formatOnSave": true,
  "python.sortImports.args": ["--line-length=100"]
}
```

## Making Contributions

### Finding Issues

- Check the [issue tracker](https://github.com/alchemiststudiosDOTai/tunacode/issues) for open issues
- Look for issues labeled `good first issue` or `help wanted`
- Comment on an issue to claim it before starting work

### Creating Issues

When creating an issue, please provide:
- Clear, descriptive title
- Detailed description of the problem or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- System information (OS, Python version, TunaCode version)

### Working on Features

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Run tests and linting**:
   ```bash
   make lint
   make test
   ```

4. **Commit your changes** using conventional commits:
   ```bash
   git commit -m "feat: add new model switching feature"
   ```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Test additions or modifications
- `chore:` - Build process or auxiliary tool changes

Examples:
```bash
feat: add OpenRouter provider support
fix: resolve file path issues on Windows
docs: update installation instructions
perf: optimize model switching speed
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these modifications:
  - Line length: 100 characters
  - Use Black for automatic formatting
  - Use isort for import sorting

### Code Quality

- **Type hints**: Use type hints for all functions and methods
- **Docstrings**: Write clear docstrings for all public functions/classes
- **Error handling**: Use appropriate exception types and provide helpful error messages
- **Logging**: Use the project's logging system instead of print statements

### Example Code Style

```python
from typing import Optional, List
from tunacode.types import Message

def process_messages(
    messages: List[Message], 
    max_tokens: Optional[int] = None
) -> List[Message]:
    """Process and validate a list of messages.
    
    Args:
        messages: List of Message objects to process
        max_tokens: Optional maximum token limit
        
    Returns:
        Processed list of messages
        
    Raises:
        ValueError: If messages are invalid
    """
    if not messages:
        raise ValueError("Messages list cannot be empty")
        
    # Implementation here
    return messages
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::TestAgent::test_model_switching
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names that explain what's being tested
- Mock external dependencies and file operations
- Aim for >80% code coverage

Example test:
```python
import pytest
from unittest.mock import Mock, patch
from tunacode.core.agents import Agent

class TestAgent:
    def test_model_switching(self):
        """Test that agent can switch models during conversation."""
        agent = Agent(model="openai:gpt-4")
        
        # Test implementation
        assert agent.current_model == "openai:gpt-4"
        
        agent.switch_model("anthropic:claude-3")
        assert agent.current_model == "anthropic:claude-3"
```

## Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and modules
- Update relevant `.md` files when making changes
- Include examples in docstrings where helpful

### Project Documentation

Key documentation files:
- `README.md` - Project overview and quick start
- `CLAUDE.md` - Instructions for Claude Code when working with the codebase
- `TUNACODE.md` - Project-specific guidelines (in user projects)
- API and architecture documentation in various `.md` files

## Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout master
   git merge upstream/master
   ```

2. **Create PR from your feature branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub with:
   - Clear title following conventional commits
   - Description of changes
   - Link to related issue(s)
   - Screenshots/demos if applicable

### PR Checklist

- [ ] Tests pass (`make test`)
- [ ] Code is linted (`make lint`)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] PR description is complete
- [ ] No merge conflicts with master branch

### Review Process

- PRs require at least one maintainer approval
- Address review feedback promptly
- Keep PRs focused - one feature/fix per PR
- Be patient - maintainers review PRs as time permits

## Getting Help

- Join discussions in [GitHub Discussions](https://github.com/alchemiststudiosDOTai/tunacode/discussions)
- Ask questions in issues (label with `question`)
- Check existing issues and PRs before creating new ones

## Recognition

Contributors are recognized in:
- The project README
- Release notes
- GitHub contributors page

Thank you for contributing to TunaCode! 🐟