# Manga2Anime

AI-powered manga to anime conversion pipeline.

## Project Status

**Current Status: Skeleton Only**

This repository contains only the initial project structure. No implementation has been done yet.

## Purpose

Manga2Anime is an AI production pipeline designed to convert manga/comic content into anime-style video scenes. The system is modular and extensible, allowing incremental development from prototype to production system.

## Architecture Overview

```
MANGA2ANIME/
├── core/           # Core data models and business logic
│   ├── project/    # Project management
│   ├── scene/      # Scene representation
│   ├── timeline/   # Timeline management
│   ├── character/  # Character system
│   ├── camera/     # Camera system
│   └── asset/      # Asset management
├── interfaces/     # Contracts between subsystems
├── tools/          # Manga, animation, VFX, audio, render tools
├── agents/         # Director, visual, audio, coder, QA agents
├── runtime/        # CLI, registry, scheduler, workers
├── apps/studio/    # Web frontend and backend
└── tests/          # Test suites
```

## Development Philosophy

### Modular First
Each subsystem has clear responsibility and interface.

### Core First
Core modules work independently without Agent, Web UI, or AI model dependencies.

### One Module at a Time
Development progresses incrementally: core/project → core/scene → core/timeline → ...

### Stability Over Speed
Priority: Correctness → Tests → Stability → Maintainability → Features

## Getting Started

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Using Docker
docker build -t manga2anime .
docker-compose up
```

## License

MIT License - see LICENSE file for details.
