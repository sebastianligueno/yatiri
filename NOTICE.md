# Notices and Attribution

## Project status

This repository currently does **not** vendor third-party source code copied into the codebase as standalone modules.

It depends on third-party libraries installed through Python packaging:

- `PyYAML`
- `prompt_toolkit`
- `rich`
- `requests`

Those dependencies keep their own licenses and terms.

## Inspirations

This project is inspired by terminal-native coding assistants and conversational CLIs, including interaction patterns familiar from tools such as Codex and Claude Code.

That inspiration refers to product interaction style and workflow, not to copied proprietary source code.

## External services

Scholar CLI can optionally use:

- DeepSeek API
- Ollama
- DuckDuckGo HTML search results for lightweight web retrieval

Users are responsible for complying with the terms of service and licenses of those external services.

## If you add third-party code later

If you later vendor templates, prompts, scripts, datasets, or source code from other projects, preserve:

- the original license;
- copyright notices;
- attribution requirements;
- any redistribution restrictions.
