# Workspace-Specific Guidance

## Testing & Task Runner

- Always run tests using the VS Code Task runner, not ad-hoc terminal commands.
- Preferred task: the default test task labeled "pytest -q" (group: test).

  - Use the IDE task runner to execute tests so output is properly parsed and shown in the Problems panel.
  - Avoid running `uv run pytest` directly unless explicitly requested.

- Static typing: also run the task "mypy".

  - Run it alongside or right after tests when code changes are made.
  - This ensures type safety with the project's strict mypy configuration.

## Shell & Output

- When shell commands must be shown (only if asked), format for fish shell and keep them copyable.
- Prefer concise output, and don’t print runnable commands unless the user requested them.
