# TinyAgent Migration - Unified LLM API Support

**Date**: 2025-05-27  
**Author**: TunaCode Development Team  
**Status**: Completed

## Overview

Successfully migrated TunaCode from pydantic-ai to tinyAgent, standardizing on the OpenAI API format for universal LLM provider support.

## Key Benefits

### 1. Unified API Interface
- All LLM providers accessed through OpenAI-compatible API format
- Simplified codebase with single integration point
- Future-proof design for new providers

### 2. Multi-Provider Support

#### Direct Support
- **OpenAI**: Native API support for GPT-4, GPT-4.1, O3 models
- **OpenRouter**: Full compatibility as OpenAI proxy for 100+ models

#### Through OpenRouter
- **Anthropic**: Claude models (Opus, Sonnet)
- **Google**: Gemini models (Flash, Pro)
- **Others**: Mistral, Meta, Cohere, and more

### 3. Implementation Details

#### API Call Flow
```
User Input → TunaCode REPL → process_request() 
→ process_request_with_tinyagent() → ReactAgent.run_react()
→ tinyAgent → OpenAI-compatible API endpoint
```

#### Model Switching
- `/model openai:gpt-4o` - Direct OpenAI API
- `/model openrouter:anthropic/claude-3-opus` - OpenRouter proxy
- Automatic environment variable management for API keys and base URLs

#### Key Files
- `src/tunacode/core/agents/tinyagent_main.py` - Core tinyAgent integration
- `src/tunacode/tools/tinyagent_tools.py` - Tool decorators
- `config.yml` - tinyAgent configuration

## Technical Architecture

### Environment Variable Routing
```python
# Direct OpenAI
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_API_KEY = "sk-..."

# OpenRouter (for all other providers)
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_API_KEY = "sk-or-..." (uses OPENROUTER_API_KEY from config)
```

### Model Format
- `provider:model` - Direct provider access
- `openrouter:provider/model` - OpenRouter proxy access

### Actual API Call
The magic happens in one line:
```python
result = await agent.run_react(message)  # Line 105 in tinyagent_main.py
```

## Migration Benefits

1. **Reduced Complexity**: Single API format instead of multiple SDKs
2. **Better Reliability**: tinyAgent's robust ReAct loop implementation
3. **Cost Optimization**: Easy switching between providers
4. **Future Compatibility**: Any OpenAI-compatible API works automatically

## Configuration

API keys stored in `~/.config/tunacode.json`:
```json
{
    "env": {
        "OPENAI_API_KEY": "sk-...",
        "OPENROUTER_API_KEY": "sk-or-...",
        "ANTHROPIC_API_KEY": "...",
        "GEMINI_API_KEY": "..."
    }
}
```

## Conclusion

The migration to tinyAgent positions TunaCode as a truly model-agnostic development tool. By standardizing on the OpenAI API format and leveraging OpenRouter as a universal proxy, users can access virtually any LLM through a single, consistent interface.

This architecture ensures TunaCode remains compatible with future LLM providers without code changes - they just need to provide an OpenAI-compatible endpoint or be available through OpenRouter.