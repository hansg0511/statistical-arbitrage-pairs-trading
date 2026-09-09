"""Compatibility entry point for the canonical experiment runner."""

from research.run_experiment import run_experiment


if __name__ == "__main__":
    raise SystemExit(run_experiment())
