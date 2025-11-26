# Shopping List Tool

A tool to parse recipes and create Amazon Fresh shopping lists with smart product matching.

## Setup

### Option 1: Automated Setup (Recommended)
```powershell
.\setup.ps1
```

This will:
- Create a virtual environment
- Install all dependencies
- Install Playwright browsers
- Activate the environment

### Option 2: Manual Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

## Usage

### Quick Test
```powershell
# Make sure venv is activated first
.\activate.ps1

# Run test script
python test_run.py
```

### Full Tool
```powershell
# Make sure venv is activated first
.\activate.ps1

# Run main tool
python main.py
```

## Features

- **Recipe Parsing**: Extracts ingredients from recipe URLs
- **Smart Matching**: Uses fuzzy matching to find best product matches
- **Confidence Scoring**: Shows 0-100% match confidence for each product
- **Amazon Fresh Integration**: Automated search and cart management
- **Session Persistence**: Saves login cookies for future runs

## Project Structure

```
shopping_list_tool/
├── venv/                    # Virtual environment (created by setup)
├── main.py                  # Main CLI application
├── parser.py                # Recipe parsing
├── shopper.py               # Amazon Fresh automation
├── utils.py                 # Utility functions
├── matcher.py               # Confidence scoring
├── test_run.py              # Test script
├── requirements.txt         # Python dependencies
├── setup.ps1                # Automated setup script
└── activate.ps1             # Quick venv activation
```

## Requirements

- Python 3.8+
- Amazon Prime account with Amazon Fresh access
- Windows (PowerShell scripts)

## Notes

- First run requires manual Amazon login (30 seconds)
- Session cookies saved to `amazon_cookies.json`
- Browser runs in visible mode by default for debugging
