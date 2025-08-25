# SEO Blog Generator (LLaMA 3 + Ollama)
This repository contains the sample code, prompts, and example outputs used in the blog.

## Contents
- `prompts.py` — System + user prompt templates.
- `generator.py` — CLI script that calls Ollama to generate Markdown blog posts.
- `requirements.txt` — Python dependencies and versions.
- `sample-titles.csv` — Example titles to batch-generate.
- `sample-output.md` — Example generated blog post.

## Quick start (Windows)
1. Install Python 3.13 and Ollama from https://ollama.com/download  
2. Make Ollama available and pull the model:
   ```bash
   ollama run llama3:8b

3. Create a virtual environment and install dependencies:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

4. Run command:
   python generator.py --title "Luxury Interior Design Ideas for Villas & Resorts" --words 1800

6. Output will be saved in /output as slug.md
