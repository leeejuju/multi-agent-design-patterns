# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python workspace for **multi-agent design pattern implementations**, based on *Agentic Design Patterns*. The repository is organized as a collection of learning modules, each demonstrating different aspects of LLM-based agent systems.

## Development Commands

All workflows use `uv` as the package manager:

- `uv sync` - Install/sync dependencies
- `uv run python <script>` - Run a module script
- `uv run ruff check .` - Lint checks
- `uv run ruff format .` - Format code
- `uv run pytest -q <path>` - Run targeted tests (avoid running entire repository)

Example: `uv run pytest -q multi-agent-framework/langchain/1-langchain-core/runnable_part`

## Module Structure

### Core Pattern Modules (`multi-agent-design-patterns/`)
Organized by lessons, each with its own `src/` structure:
- `lesson1_ordinary_agent/` - Basic agent architecture with BaseAgent and BaseContext
- `src/agents/common/` - Base agent classes, context management, and middleware
- `src/agents/deepagents/` - DeepAgents framework integration
- `src/configs/` - Model provider configurations (Pydantic-based)
- `src/utils/` - Utility functions

### Framework Implementations (`multi-agent-framework/`)
- `langchain/` - LangChain framework examples and runnable patterns
- AgentScope and other framework integrations

### Supporting Modules
- `multi-agent-memory/` - Memory system implementations
- `llm-rag/` - Retrieval-Augmented Generation implementations
- `llm-lab/` - Model experimentation
- `vibecoding-workshop/` - Workshop materials

## Architecture Patterns

### Base Agent System
- `BaseAgent` - Base class with `name`, `description`, `context`, and `stream_messages()` method
- `BaseContext` - Dataclass for managing agent state with `update()`, `get_context()`, and serialization methods
- `ModelProvider` - Pydantic model for LLM configuration (name, api_key, base_url)

### Framework Integration
- **LangChain**: Runnable patterns (RunnableParallel, RunnableEach, etc.)
- **LangGraph**: Workflow and state management
- **DeepAgents**: Alternative agent framework implementation

## Coding Standards

- Python: `>=3.13`
- Line length: 100 characters
- Double quotes for strings
- Snake_case for functions/files, PascalCase for classes, UPPER_CASE for constants
- Use `uv` for all dependency management

## Commit Conventions

Follows Conventional Commits with **English descriptions**:
- Format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `perf`, `ci`, `build`
- Examples:
  - `feat(evermemos): add memory storage feature`
  - `docs(lesson1): update README about XXX`
  - `chore: update pyproject.toml dependencies`

## Environment Configuration

Use `.env.example` as template. Key variables:
- LLM API keys: `SILICONFLOW_API_KEY`, `DASHSCOPE_API_KEY`, `GEMINI_API_KEY`
- PostgreSQL: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `SAVE_DIR` - Path for saving agent outputs

## Key Dependencies

- `langchain>=1.2.0` - Core framework
- `langgraph>=1.0.5` - Workflow orchestration
- `deepagents>=0.4.3` - Agent framework
- `pgvector>=0.4.2` - Vector storage for PostgreSQL
- `pydantic-settings>=2.11.0` - Configuration management
