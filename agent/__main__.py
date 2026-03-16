"""
Entry point for running the agent as a module.

Usage:
    python -m agent                 # Run the agent loop
    python -m agent --test-schedule # Show scheduled tasks
    python -m agent --init-tasks    # Initialize default tasks
"""

from .loop import main

if __name__ == "__main__":
    main()
