#!/usr/bin/env python3
"""
Polar Loop Data Analyzer
Main entry point for the application.
"""

import sys
from pathlib import Path
from src.presentation.app import PolarAnalyzerApp


def main():
    """Main entry point."""
    try:
        # Check if data directory exists
        data_dir = Path("loop_data")
        if not data_dir.exists():
            print(f"Error: Data directory '{data_dir}' not found.")
            print("Please ensure your Polar Loop data is in the 'loop_data' directory.")
            sys.exit(1)

        # Check if any JSON files exist
        json_files = list(data_dir.glob("*.json"))
        if not json_files:
            print(f"Error: No JSON files found in '{data_dir}'.")
            print("Please export your Polar Loop data and place it in the 'loop_data' directory.")
            sys.exit(1)

        # Run the TUI application
        app = PolarAnalyzerApp()
        app.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()