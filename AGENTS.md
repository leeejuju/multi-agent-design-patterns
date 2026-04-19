# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python workspace with multiple learning modules. Top-level folders group topics by domain:
- `multi-agent-design-patterns/`: core pattern demos (for example `lesson1_ordinary_agent/src/agents`, `src/configs`, `src/utils`).
- `multi-agent-framework/`, `multi-agent-memory/`, `llm-rag/`, `llm-lab/`: framework, memory, RAG, and model labs.
- `vibecoding-workshop/`: workshop notes/examples.
- Root config files: `pyproject.toml`, `uv.lock`, `.env.example`.

Prefer adding new code inside the closest existing module instead of creating new top-level directories.

## Build, Test, and Development Commands
Use `uv` for all local workflows:
- `uv sync`: install/sync dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python <path_to_script.py>`: run a module or example script.
- `uv run ruff check .`: run lint checks.
- `uv run ruff format .`: auto-format code.
- `uv run pytest -q <target_path>`: run targeted tests first (avoid running the whole repo by default).

Example: `uv run pytest -q multi-agent-framework/langchain/1-langchain-core/runnable_part`.

## Coding Style & Naming Conventions
- Python version: `>=3.13`.
- Ruff settings: line length `100`, double quotes, spaces for indentation.
- Naming: `snake_case` for functions/files, `PascalCase` for classes, `UPPER_CASE` for constants.
- Design from first principles: start with the simplest version that satisfies the current requirement.
- Do not add abstractions, defensive branches, extension points, or "just in case" code unless they are required now.
- For business scripts and one-off workflows, write the smallest direct implementation that completes the task; do not add defensive compatibility layers unless the current data or caller requires them.
- If a proposed change clearly follows first-principles simplification, execute it directly without asking for extra confirmation.
- Keep changes minimal and local; avoid broad refactors unless requested.
- Add comments only for non-obvious logic.

## Assistant Response Style
- Default to brief, direct answers.
- Prefer the minimum explanation needed to solve the user's request.
- Expand only when the user explicitly asks for more detail, examples, or reasoning.
- Avoid restating obvious context or adding extra background unprompted.
- Keep the tone restrained and neutral.
- Prioritize concise, clear answers over warmth or conversational filler.
- Use a serious, professional tone.
- Do not use colloquial acknowledgement/closure phrases such as "我知道了", "好的", or "完毕".

## Testing Guidelines
Pytest is used where tests exist (many modules are example-driven and may not have full coverage).
- Place tests near the related module or in its existing test location.
- Test file names: `test_*.py`.
- Run smallest relevant test scope before broader runs.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit prefixes, mainly `feat:`, `docs:`, `chore:` (and occasionally `fix:`).
- Commit format: `<type>(optional-scope): <short description>`.
- Keep one logical change per commit.
- PRs should include: summary, affected paths, validation commands/results, and linked issue (if any).
- Include screenshots only for UI/documentation visuals.

## Security & Configuration Tips
- Do not commit secrets; use `.env.example` as template.
- Do not modify lockfiles/dependencies unless the task requires it.
- Avoid changing CI/release files unless explicitly requested.
