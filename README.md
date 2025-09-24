# Polar Loop Data Analyzer

A Python TUI application for analyzing Polar Loop fitness band data with heart rate graphics, trends, and activity statistics.

## Features

- **Heart Rate Analysis**: Real-time heart rate monitoring with trend analysis
- **Activity Tracking**: METs, calories, and activity level monitoring
- **Zone Distribution**: Heart rate zone analysis (Rest, Light, Moderate, Hard, Maximum)
- **Trend Analysis**: 7-day trend visualization and statistics
- **Data Persistence**: SQLite database for efficient data storage
- **Clean Architecture**: Repository, Service, and Facade design patterns

## Architecture

The application follows clean architecture principles with clear separation of concerns:

### Design Patterns Implemented

1. **Repository Pattern**: Abstracts data access (JSON reading and SQLite persistence)
2. **Service Layer**: Encapsulates business logic for heart rate and statistics
3. **Facade Pattern**: Provides simplified API for complex subsystem operations
4. **Domain Models**: Clean domain entities using Pydantic for validation

### Project Structure

```
src/
├── domain/          # Domain models and value objects
├── repository/      # Data access layer (JSON & SQLite)
├── service/         # Business logic layer
├── infrastructure/  # Database and configuration
├── presentation/    # TUI layer with Textual
│   ├── views/      # Dashboard and other views
│   └── components/ # Reusable UI components
├── facade.py       # Simplified API facade
└── main.py         # Application entry point
```

## Installation

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

## Usage

1. Place your Polar Loop exported JSON data in the `loop_data/` directory

2. Run the application:
```bash
poetry run python -m src.main
```

Or directly:
```bash
poetry run polar-analyzer
```

## Keyboard Shortcuts

- `q` - Quit application
- `r` - Refresh dashboard
- `d` - Toggle dark mode
- `Tab` - Switch between tabs

## Data Flow

1. **Import**: JSON files are read from `loop_data/` directory
2. **Transform**: Data is parsed into domain models with validation
3. **Persist**: Normalized data is stored in SQLite database
4. **Query**: Services retrieve data via repositories
5. **Present**: Facade provides simple API for TUI components

## Dependencies

- `textual`: Terminal UI framework
- `rich`: Terminal formatting and styling
- `plotext`: Terminal plotting library
- `sqlalchemy`: Database ORM
- `pydantic`: Data validation and models

## Development

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black src/
```

Type checking:
```bash
poetry run mypy src/
```