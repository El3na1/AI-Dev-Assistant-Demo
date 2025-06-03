#!/usr/bin/env python3
import os
import openai
import requests
import sys

import json

event_path = os.getenv("GITHUB_EVENT_PATH")
if not event_path or not os.path.exists(event_path):
    print("Error: GITHUB_EVENT_PATH not found.")
    sys.exit(1)
    
with open(event_path, "r") as f:
    event = json.load(f)

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")  # e.g., user/repo
PR_NUMBER = event["pull_request"]["number"]  # Extract PR number
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Step 1: Get pull request diff
diff_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}"
diff_response = requests.get(diff_url, headers=headers)

if diff_response.status_code != 200:
    print("Failed to fetch PR info:", diff_response.text)
    sys.exit(1)

pr_data = diff_response.json()
diff_url = pr_data.get("diff_url")
diff_text = requests.get(diff_url, headers=headers).text

# Step 2: Send to OpenAI
prompt = f"""You are an experienced C# code reviewer.
Review the following pull request diff and return a JSON array of review comments like this:

[
  {{
    "file": "filename.cs",
    "line": 12,
    "comment": "Consider renaming this method to follow PascalCase."
  }}
]

Diff:
{diff_text}
"""

completion = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)

try:
    suggestions = eval(completion["choices"][0]["message"]["content"])  # Use JSON-safe parsing in production
except Exception as e:
    print("Failed to parse GPT response:", e)
    sys.exit(1)

# Step 3: Post comments to PR
for s in suggestions:
    file_path = s["file"]
    line = s["line"]
    body = s["comment"]

    comment_payload = {
        "body": body,
        "path": file_path,
        "line": line,
        "side": "RIGHT"
    }

    comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}/comments"
    r = requests.post(comments_url, headers=headers, json=comment_payload)

    if r.status_code not in [200, 201]:
        print(f"Failed to comment on {file_path}:{line} - {r.status_code}: {r.text}")
    else:
        print(f"Comment posted to {file_path}:{line}")
