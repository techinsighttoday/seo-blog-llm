import re
import os
from datetime import datetime
from slugify import slugify
import ollama  # pip install ollama
from prompts import SYSTEM_PROMPT, USER_TEMPLATE
import argparse

MODEL_NAME = "llama3:8b"  # adjust if you pulled a different tag
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)

def build_user_prompt(
    title: str,
    word_count: int = 1500,
    audience: str = "beginner bloggers and content marketers",
    geo: str = "global",
    primary_kw: str = None,
    secondary_kws: list[str] = None,
):
    if primary_kw is None:
        primary_kw = title.lower()
    if secondary_kws is None:
        secondary_kws = []
    secondary_str = ", ".join(secondary_kws) if secondary_kws else "n/a"
    return USER_TEMPLATE.format(
        title=title,
        word_count=word_count,
        audience=audience,
        geo=geo,
        primary_kw=primary_kw,
        secondary_kws=secondary_str
    )

def call_llm(system_prompt: str, user_prompt: str, temperature=0.4, num_ctx=8192):
    # Chat-style call for better instruction-following
    resp = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": temperature,
            "num_ctx": num_ctx,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
        stream=False,
    )
    return resp["message"]["content"]

def validate_front_matter(md: str):
    """
    Basic YAML front matter extraction and checks for meta length.
    """
    fm = re.search(r"^---\s*(.*?)\s*---", md, re.DOTALL | re.MULTILINE)
    issues = []
    meta = {}

    if not fm:
        issues.append("Missing YAML front matter block ('---').")
        return meta, issues

    block = fm.group(1)
    # naive parse (keep simple for no dependencies)
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    # checks
    mt = meta.get("meta_title", "")
    mdsc = meta.get("meta_description", "")
    if len(mt) > 60:
        issues.append(f"meta_title too long ({len(mt)} chars).")
    if len(mdsc) > 160:
        issues.append(f"meta_description too long ({len(mdsc)} chars).")
    if "slug" not in meta or not meta["slug"]:
        # fall back to title-based slug if needed
        title_match = re.search(r'Title:\s*"([^"]+)"', md)
        fallback = slugify(title_match.group(1)) if title_match else f"post-{datetime.now().strftime('%Y%m%d%H%M')}"
        meta["slug"] = fallback
        issues.append("Missing slug; auto-generated.")
    return meta, issues

def ensure_headers(md: str):
    if "## " not in md:
        return ["No H2 headers found."]
    return []

def save_article(md: str, slug: str | None = None):
    if not slug:
        slug = slugify("article-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    path = os.path.join(OUT_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    return path

def generate_blog(
    title: str,
    word_count: int = 1500,
    audience: str = "beginner bloggers and content marketers",
    geo: str = "global",
    primary_kw: str | None = None,
    secondary_kws: list[str] | None = None,
):
    user_prompt = build_user_prompt(
        title=title,
        word_count=word_count,
        audience=audience,
        geo=geo,
        primary_kw=primary_kw,
        secondary_kws=secondary_kws or [],
    )
    md = call_llm(SYSTEM_PROMPT, user_prompt)
    meta, fm_issues = validate_front_matter(md)
    hdr_issues = ensure_headers(md)

    issues = fm_issues + hdr_issues
    path = save_article(md, meta.get("slug"))

    return {
        "path": path,
        "meta": meta,
        "issues": issues
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SEO blog from title")
    parser.add_argument("--title", required=True, help="Blog title")
    parser.add_argument("--words", type=int, default=1500, help="Target word count")
    args = parser.parse_args()

    result = generate_blog(
        title=args.title,
        word_count=args.words,
        primary_kw=args.title.lower(),  # simple default keyword
        secondary_kws=[],
    )

    print("✅ Saved:", result["path"])
    if result["issues"]:
        print("⚠️ Validation notes:")
        for i in result["issues"]:
            print("-", i)
