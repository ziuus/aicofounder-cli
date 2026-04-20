# AICoFounder CLI (Gemini Bridged)

A powerful, standalone Python CLI application that acts as your AI Co-Founder. It performs deep web research, validates your startup ideas, roasts your weak assumptions, and provides a concrete blueprint for building your product—all using your existing **Gemini CLI** authentication.

## Features

- **Gemini CLI Bridge**: No separate API keys or quotas to manage. It uses your existing `gemini` login.
- **Rich Terminal UI**: Gorgeous formatting, spinners, and Markdown rendering powered by `rich`.
- **Autonomous Research**: Free, real-time web scraping using `duckduckgo-search` to find direct competitors and market data.
- **Brutal Validation**: Critically analyzes your idea, points out flaws, identifies your USP, and gives you a tech stack roadmap.
- **MVP Codebase Validation**: (New!) Analyze your existing repository to audit your code's scalability, technical debt, and implementation maturity.
- **Auto-Reports**: Saves a detailed `.md` report of your validation session to your local machine.

## Installation

1. Make sure you have Python 3 installed and the **Gemini CLI** authenticated.
2. Create a virtual environment and install dependencies:
   ```bash
   cd ~/Projects/aicofounder-cli
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Run the CLI tool:

```bash
source venv/bin/activate
python main.py
```



If it doesnt work

```bash
./venv/bin/python main.py 
```

Follow the interactive prompts to share your idea, target audience, and current progress!

## How it works
This tool invokes the `gemini` command in headless mode (`gemini -p "..." --output-format json`) to perform AI analysis. This means it inherits your current login session, safety settings, and AI models from the Gemini CLI.
