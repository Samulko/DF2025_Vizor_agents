# OpenTelemetry Quick Start

## Test Basic Setup
```bash
# Test span generation works
uv run python test_span_generation.py

# Test smolagents instrumentation
uv run python test_smolagents_instrumentation.py
```

## Run with Different Backends

### Console (Debug Mode)
```bash
OTEL_BACKEND=console uv run python -m bridge_design_system.main --test
```

### Phoenix (with UI)
```bash
# Terminal 1: Start Phoenix server
python -m phoenix.server.main serve

# Terminal 2: Run with Phoenix
OTEL_BACKEND=phoenix uv run python -m bridge_design_system.main --test
```

### Langfuse (Cloud)
```bash
# Add to .env:
# LANGFUSE_PUBLIC_KEY=your_key
# LANGFUSE_SECRET_KEY=your_secret

OTEL_BACKEND=langfuse uv run python -m bridge_design_system.main --test
```

### Hybrid (LCARS + Langfuse)
```bash
# Default mode - best for normal use
uv run python -m bridge_design_system.main --interactive
```

## Environment Setup
Add to `.env`:
```
OTEL_ENABLED=true
OTEL_BACKEND=hybrid
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
```

## Test All Backends
```bash
uv run python test_hybrid_backend.py
uv run python test_phoenix_backend.py
```