# Gemini Project: AI智能书签分类系统

This document provides context for the Gemini agent to understand and work with this project.

## Project Overview

This project is an intelligent bookmark management system named "AI智能书签分类系统 v2.0". It uses a combination of a rule engine and machine learning to automatically classify and organize browser bookmarks.

Key features include:
- AI-powered classification using rules and ML.
- High-performance parallel processing.
- Duplicate bookmark detection.
- A rich interactive Command Line Interface (CLI).
- Flexible configuration via a `config.json` file.

## Key Files

- **`main.py`**: The main entry point for the application. It handles command-line argument parsing and orchestrates the overall process.
- **`config.json`**: The central configuration file. It defines classification categories, rules, AI settings, and processing order.
- **`requirements.txt`**: A list of all Python dependencies required for the project.
- **`src/`**: The main source code directory.
    - **`ai_classifier.py`**: Core logic for the AI-based classification.
    - **`bookmark_processor.py`**: Handles the processing of bookmark files.
    - **`cli_interface.py`**: Implements the interactive CLI using the `rich` library.
    - **`rule_engine.py`**: The engine for rule-based classification.
    - **`ml_classifier.py`**: The machine learning classification module.
- **`tests/input/`**: The default directory for input bookmark files (`.html`).
- **`results/`**: The default directory for output files (`.html`, `.json`, `.md`).
- **`README.md`**: Contains detailed information about the project, setup, and usage.

## How to Run

### 1. Install Dependencies

To install the necessary Python packages, run:
```bash
pip install -r requirements.txt
```

### 2. Run the Application

The application can be run in two main modes:

**Interactive Mode (Recommended):**
This mode provides a user-friendly menu to access all features.
```bash
python main.py --interactive
```

**Command-Line Mode:**
This mode is suitable for scripting and automation.
```bash
# Process a single bookmark file
python main.py -i tests/input/your_bookmarks.html

# Process multiple files and train the ML model
python main.py -i tests/input/*.html --train
```

### 3. Health Check

The project includes a health check script to verify the environment and dependencies.
```bash
python src/health_checker.py
```
or
```bash
python main.py --health-check
```

## Common Commands

- **Run in interactive mode:** `python main.py --interactive`
- **Process bookmarks:** `python main.py -i <path_to_bookmarks.html>`
- **Install dependencies:** `pip install -r requirements.txt`
- **Run health check:** `python main.py --health-check`
- **Train the model:** `python main.py -i <path_to_bookmarks.html> --train`
