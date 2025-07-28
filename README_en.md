[中文](./README.md)

# Bookmark Steward

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python script that automatically merges, cleans, and categorizes browser bookmarks.
**The core of this project is an open, community-driven rules library (`config.json`)** that powers a weight-based intelligent engine, aiming to be the most comprehensive and rational solution for automatic bookmark organization.

## ✨ Key Features

- **Weight-Based Intelligent Scoring Engine**: Say goodbye to simple keyword matching! This tool evaluates a bookmark's domain, URL, title, and other information to calculate a score for each possible category, choosing the one with the highest score as the final destination. This significantly improves classification accuracy and rationality.
- **Community-Driven Rule Library**: The core `config.json` file is open and collaborative. We encourage users to contribute rules to help it evolve and cover more domains.
- **Multi-Dimensional Classification**: Finely categorizes bookmarks based on both **content format** (e.g., video, document, code repository) and **content theme** (e.g., tech, design, news).
- **Multi-Strategy Management**: Supports creating multiple `config_*.json` strategy files, allowing you to choose the one you need at runtime to easily handle different scenarios (e.g., work, study, personal).
- **Full Automation**: From automatic merging, deduplication, and URL cleaning to generating importable `HTML` and readable `Markdown` files, the entire process is automated.

## 🚀 Quick Start

**Get started with powerful, automatic organization in just 3 steps.**

1.  **Prepare the Project**: Clone the repository and install dependencies.
    ```bash
    git clone https://github.com/YOUR_USERNAME/CleanBookmarks.git
    cd CleanBookmarks
    pip install -r requirements.txt
    ```
2.  **Add Your Bookmarks**: Place all your exported `.html` bookmark files from your browser into the `tests/input` folder.
3.  **Run the Script**:
    ```bash
    python src/clean_marks.py
    ```
    The script will automatically use the default `config.json` rule library. If multiple strategy files are detected, you will be prompted to choose one. The organized files will be output to the `tests/output` directory.

---

## ❤️ Contribute Rules: Build the Strongest Brain

We believe the best classification rules come from the real-world needs of thousands of users. Contributing rules is the most important way to contribute to this project, and it requires no coding.

**How to Contribute**: Fork this project -> Edit `config.json` -> Create a Pull Request.

### Understanding the Rule Structure

The core of `config.json` is `category_rules`, which defines the logic for theme-based classification. Each category is driven by a `rules` array:

```json
"Tech/Backend & Databases": {
    "rules": [
        { 
            "match": "domain", 
            "keywords": ["python.org", "rust-lang.org"], 
            "weight": 10 
        },
        { 
            "match": "title", 
            "keywords": ["python", "golang", "go", "rust"], 
            "weight": 5, 
            "must_not_contain": ["game", "play rust"] 
        },
        { 
            "match": "title", 
            "keywords": [" go "],  // Note the spaces around "go" for precise word matching
            "weight": 4, 
            "must_not_contain": ["go out", "go shopping"] 
        }
    ]
}
```

- `match`: Specifies the target to match, can be `domain`, `url` (full link), or `title`.
- `keywords`: A list of keywords.
- `weight`: **The core of the intelligent scoring.** **Domain matches should typically have the highest weight** as they are the most accurate. Title matches should have a relatively lower weight.
- `must_not_contain`: **A list of exclusion words.** If any of these words appear in the matched target, this rule will be ignored (score of zero). This is crucial for eliminating ambiguity (e.g., distinguishing the programming language `Rust` from the game `Rust`).

You can modify existing rules or add new categories following this structure to make our "brain" smarter!

## 🛠️ Advanced Usage: Multi-Strategy Management

You can create multiple `config_*.json` files (e.g., `config_work.json`, `config_personal.json`), with each file representing a separate set of classification strategies.

When you run the script directly, it will automatically detect these files and provide a menu for you to select the strategy for the current session (press Enter to use the default `config.json`). You can also force a specific configuration file using the `--config` parameter.

## 📜 License

This project is licensed under the [MIT License](LICENSE). 