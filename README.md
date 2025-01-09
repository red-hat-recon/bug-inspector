# Bug Inspector

## Overview
Bug Inspector is a Python-based tool that leverages GPT to analyze source code for potential security issues. It uses a set of prompts to evaluate specific aspects of the code and generates a detailed JSON report.

## Features
- Splits large source code files into manageable chunks (max 8000 words per chunk).
- Uses GPT's API with `SYSTEM` and `USER` prompts for comprehensive analysis.
- Saves results for each prompt in individual JSON files.
- Provides a combined JSON result for all analyses.

## Requirements
- Python 3.7+
- OpenAI API key

## Setup

1. **Clone the Repository:**
   ```bash
    git clone https://github.com/your-repo/bug-inspector.git
    cd bug-inspector
   ```

2. **Install the Dependencies:**
    ```bash
    pip install requests python-dotenv pyyaml
    OR
    pip3 install -r requirements.txt
    ```

3. **Set Up .env: Create a .env file in the config directory and add your OpenAI API key:**
    ```bash
    echo "OPENAI_API_KEY=your_openai_api_key_here" > config/.env
    ```
    Have a look at .env_example file for example

4. **Add Prompts:**
    Update the prompts in prompts/prompt-config.yaml.

5. **Run the script:**
    ```bash
    python src/bug_inspector.py
    ```
