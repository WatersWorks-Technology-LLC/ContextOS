# Contributing to ContextOS

Thank you for your interest in contributing to **ContextOS**! We welcome contributions from developers, researchers, and open-source enthusiasts.

## How to Get Started

1. **Fork & Clone the Repository**:
   ```bash
   git clone https://github.com/WatersWorks-Technology-LLC/ContextOS.git
   cd ContextOS
   ```
2. **Set Up Your Environment**:
   ```bash
   pip install -e .
   ```
3. **Hydrate Local Ollama Coprocessor**:
   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen2.5:1.5b
   ```
4. **Run the Test Suite**:
   ```bash
   PYTHONPATH=src pytest tests/unit/ tests/integration/ tests/live/
   ```

## Key Focus Areas for Contributors

- **Heterogeneous Codecs & Representations**: Expanding NCC-VCL and VCL-A compact textual/visual context representation formats.
- **Local LLM Coprocessor Optimization**: Benchmarking local Ollama / vLLM / llama.cpp models for faster IR extraction and reranking.
- **Agent Runtime Adapters**: Building native integrations for AutoGen, CrewAI, LangGraph, and Cursor.
- **Context Benchmarking**: Designing stress tests for 1,000+ turn agent sessions and measuring drift reduction.
- **Developer Experience & CLI**: Enhancing `contextos status --watch` real-time terminal TUI monitors.

## Pull Request Guidelines

- Ensure all existing unit and integration tests pass cleanly.
- Add test coverage for any new features or bug fixes under `tests/unit/` or `tests/integration/`.
- Maintain docstrings and preserve strict 5-part identity key isolation rules.

