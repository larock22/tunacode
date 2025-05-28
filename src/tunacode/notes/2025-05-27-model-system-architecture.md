# Model System Architecture

The repo relies on pydantic-ai to talk to language models. When the REPL needs a model, it constructs a pydantic_ai.Agent with a model name such as openai:gpt-4o or openrouter:openai/gpt-4.1:

```python
def get_or_create_agent(model: ModelName, state_manager: StateManager) -> PydanticAgent:
    if model not in state_manager.session.agents:
        max_retries = state_manager.session.user_config["settings"]["max_retries"]
        state_manager.session.agents[model] = Agent(
            model=model,
            tools=[
                Tool(read_file, max_retries=max_retries),
                Tool(run_command, max_retries=max_retries),
                Tool(update_file, max_retries=max_retries),
                Tool(write_file, max_retries=max_retries),
            ],
            mcp_servers=get_mcp_servers(state_manager),
        )
```

The active model defaults to OpenAI's GPT‑4o:

```python
current_model: ModelName = "openai:gpt-4o"
```

Model configurations—including OpenAI and OpenRouter variants—are defined in configuration/models.py:

```python
"openai:gpt-4.1": ModelConfig(...),
"openai:gpt-4o": ModelConfig(...),
"openrouter:mistralai/devstral-small": ModelConfig(...),
"openrouter:openai/gpt-4.1": ModelConfig(...),
```

User configuration specifies API keys for both providers and sets the default model to an OpenRouter entry:

```python
DEFAULT_USER_CONFIG: UserConfig = {
    "default_model": "openrouter:openai/gpt-4.1",
    "env": {
        "ANTHROPIC_API_KEY": "",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "OPENROUTER_API_KEY": "",
    },
    ...
}
```

During setup, EnvironmentSetup copies these env values into os.environ, so the underlying OpenAI client (used by pydantic-ai) picks them up:

```python
for key, value in env_dict.items():
    ...
    if value:
        os.environ[key] = value
```

To send requests through OpenRouter, the README instructs running the CLI with OPENAI_BASE_URL=https://openrouter.ai/api/v1 and providing OPENROUTER_API_KEY:

### OpenRouter Support
To use OpenRouter models, add an `OPENROUTER_API_KEY`…
```bash
OPENAI_BASE_URL="https://openrouter.ai/api/v1" tunacode
/model openrouter:mistralai/devstral-small
/model openrouter:openai/gpt-4.1-mini
/model openrouter:codex-mini-latest
```

In short, the codebase doesn't call OpenAI or OpenRouter APIs directly. Instead it relies on pydantic-ai.Agent, which reads the chosen model name and environment variables. Setting OPENAI_API_KEY uses OpenAI's API at the default base URL, while setting OPENAI_BASE_URL to OpenRouter's endpoint and providing OPENROUTER_API_KEY routes those same requests through the OpenRouter service.