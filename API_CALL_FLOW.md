# API Call Flow in TunaCode with tinyAgent

## 1. User Input → TunaCode
```python
# In repl.py
line = await ui.multiline_input(state_manager, _command_registry)
# User types: "Read the README file"
```

## 2. TunaCode → process_request
```python
# In repl.py
res = await agent.process_request(
    state_manager.session.current_model,  # e.g., "openai:gpt-4o"
    text,                                  # "Read the README file"
    state_manager,
    tool_callback=tool_callback_with_state,
)
```

## 3. process_request → TinyAgent Wrapper
```python
# In core/agents/main.py
async def process_request(...):
    result = await process_request_with_tinyagent(
        model, message, state_manager, tool_callback
    )
```

## 4. TinyAgent Setup
```python
# In core/agents/tinyagent_main.py
agent = get_or_create_react_agent(model, state_manager)

# This creates/retrieves a ReactAgent with:
# - model_override set to the actual model name
# - Environment variables configured (OPENAI_BASE_URL, API keys)
# - Tools registered (read_file, write_file, etc.)
```

## 5. THE ACTUAL API CALL
```python
# In core/agents/tinyagent_main.py, line 105
result = await agent.run_react(message)
```

### What happens inside `agent.run_react()`:

1. **ReactAgent** (from tinyAgent) processes the message
2. It uses the configured model (e.g., "gpt-4o")
3. It reads environment variables:
   - `OPENAI_API_KEY` or `OPENROUTER_API_KEY`
   - `OPENAI_BASE_URL` (https://api.openai.com/v1 or https://openrouter.ai/api/v1)
4. Makes HTTP request to the API endpoint
5. Handles tool calls if needed
6. Returns the response

## 6. Example API Request (what tinyAgent sends)
```http
POST https://api.openai.com/v1/chat/completions
Authorization: Bearer sk-...
Content-Type: application/json

{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "Read the README file"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_file",
        "description": "Read the contents of a file",
        "parameters": {...}
      }
    },
    // ... other tools
  ]
}
```

## 7. Model Switching Example
When user runs `/model openrouter:openai/gpt-4.1`:

1. Next API call will use:
   - URL: `https://openrouter.ai/api/v1/chat/completions`
   - Model: `"openai/gpt-4.1"`
   - API Key: From `OPENROUTER_API_KEY` in config

The actual HTTP request is made by tinyAgent's internal OpenAI client when `agent.run_react()` is called.