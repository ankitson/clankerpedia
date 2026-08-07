# Documentation and work-logging
- See the document-work skill

# Testing
- Prefer writing and extending reusable unit and integration tests over one-off scripting. 

# Scripting
- Prefer python or typescript/javascript over bash unless absolutely necessary or its a very simple script
- When appropriate, create a Justfile with commonly used commands and keep it up to date. This file must not become a dumping ground for every command and must be kept organized and focused.

# Programming Language Guidance

## Python
- Prefer `uv` over other tools
- Prefer PEP 723 inline metadata for dependencies in small scripts, and use a `pyproject.toml` file for more complex projects

## Javascript
- Prefer `bun` and typescript over other tools
