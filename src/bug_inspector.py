import os
import yaml
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../config/.env")

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1/chat/completions")
MODEL = os.getenv("MODEL", "gpt-4")
MAX_CHUNK_SIZE = 8000  # Maximum chunk size for source code (in words)
RETRY_LIMIT = 3  # Number of retries for failed API calls

# Load configuration from YAML file
def load_config(config_path: str):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

# Load prompts from configuration file
def load_prompts(prompt_config_path: str):
    with open(prompt_config_path, "r") as file:
        return yaml.safe_load(file).get("prompts", [])

# Split source code into chunks
def split_source_code(source_code: str, max_words: int):
    words = source_code.split()
    chunks = [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]
    return chunks

# Make GPT API call
def gpt_api_call(system_prompt, user_prompt, retries=0):
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = requests.post(BASE_URL, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for non-200 responses
        return response.json()
    except Exception as e:
        if retries < RETRY_LIMIT:
            print(f"Retrying API call ({retries + 1}/{RETRY_LIMIT}) due to error: {e}")
            return gpt_api_call(system_prompt, user_prompt, retries + 1)
        else:
            raise

# Process a single source code file
def process_file(file_path, prompts, input_dir, output_dir):
    print(f"Processing file: {file_path}")
    results = {}
    try:
        # Load source code
        with open(file_path, "r") as file:
            source_code = file.read()

        # Split source code into chunks
        code_chunks = split_source_code(source_code, MAX_CHUNK_SIZE)

        for chunk_idx, chunk in enumerate(code_chunks, start=1):
            # Write input chunk to file
            input_chunk_file = f"{input_dir}/chunk_{chunk_idx}_{Path(file_path).stem}.txt"
            with open(input_chunk_file, "w") as input_file:
                input_file.write(chunk)

            for i, prompt in enumerate(prompts, start=1):
                print(f"Running chunk {chunk_idx}/{len(code_chunks)}, prompt {i}/{len(prompts)}")
                system_prompt = prompt.get("system", "")
                # Use triple double quotes for input source
                user_prompt = f"""{prompt.get('user', '')}\n\nSource Code Chunk:\n\"\"\"{chunk}\"\"\""""
                try:
                    result = gpt_api_call(system_prompt, user_prompt)
                    result_yaml = result["choices"][0]["message"]["content"]

                    # Parse YAML safely
                    try:
                        parsed_result = yaml.safe_load(result_yaml)
                    except yaml.YAMLError as parse_error:
                        print(f"YAML parsing error for chunk {chunk_idx}, prompt {i}: {parse_error}")
                        parsed_result = {"error": "YAML parsing failed", "raw_output": result_yaml}

                    result_key = f"{Path(file_path).stem}_chunk_{chunk_idx}_prompt_{i}"
                    results[result_key] = parsed_result

                    # Save individual result to a YAML file
                    output_file_path = f"{output_dir}/result_{result_key}.yaml"
                    with open(output_file_path, "w") as output_file:
                        yaml.dump(parsed_result, output_file, default_flow_style=False)
                except Exception as e:
                    print(f"Error processing chunk {chunk_idx}, prompt {i}: {e}")
                    results[f"{Path(file_path).stem}_chunk_{chunk_idx}_prompt_{i}"] = {"error": str(e)}
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

    return results

# Inspect source code from files and directories
def inspect_source_code(input_sources, prompts, input_dir, output_dir):
    results = {}
    for source in input_sources:
        source_path = Path(source)
        if source_path.is_dir():
            # Process all files in the directory
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    file_results = process_file(file_path, prompts, input_dir, output_dir)
                    results.update(file_results)
        elif source_path.is_file():
            # Process a single file
            file_results = process_file(source, prompts, input_dir, output_dir)
            results.update(file_results)
        else:
            print(f"Invalid source: {source}")

    # Save all results to a combined YAML file
    combined_results_path = f"{output_dir}/combined_results.yaml"
    with open(combined_results_path, "w") as output_file:
        yaml.dump(results, output_file, default_flow_style=False)

    print(f"Inspection completed. Results saved in {output_dir}/combined_results.yaml")

# Main function
def main():
    # Load configuration
    config_path = "../config/config.yaml"
    config = load_config(config_path)

    input_sources = config.get("input_source", [])
    base_output_dir = Path(config.get("output_directory", "../outputs"))
    prompt_config_path = config.get("prompt_config_path", "../prompts/prompt-config.yaml")

    # Create output directories with timestamps
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_dir = base_output_dir / f"inputs_{timestamp}"
    output_dir = base_output_dir / f"outputs_{timestamp}"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load prompts
    prompts = load_prompts(prompt_config_path)

    # Run inspection
    inspect_source_code(input_sources, prompts, input_dir, output_dir)

if __name__ == "__main__":
    main()
