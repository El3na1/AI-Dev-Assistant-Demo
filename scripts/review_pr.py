#!/usr/bin/env python3
import os
import sys
import json
import requests
from openai import OpenAI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        print(f"Error: Missing environment variable {name}")
        sys.exit(1)
    return value

GITHUB_REPO = get_env_var("GITHUB_REPOSITORY")
GITHUB_TOKEN = get_env_var("GITHUB_TOKEN")
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
EVENT_PATH = get_env_var("GITHUB_EVENT_PATH")

# Load PR number from event payload
try:
    with open(EVENT_PATH, "r") as f:
        event = json.load(f)
    PR_NUMBER = event["pull_request"]["number"]
except Exception as e:
    print(f"Error reading PR number from event payload: {e}")
    sys.exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_pr_diff():
    diff_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}"
    pr_response = requests.get(diff_url, headers=headers)
    if pr_response.status_code != 200:
        print("Failed to fetch PR info:", pr_response.text)
        sys.exit(1)
    pr_data = pr_response.json()
    diff_url = pr_data.get("diff_url")
    if not diff_url:
        print("No diff URL found in PR data.")
        sys.exit(1)
    diff_response = requests.get(diff_url, headers=headers)
    if diff_response.status_code != 200:
        print("Failed to fetch diff:", diff_response.text)
        sys.exit(1)
    return diff_response.text

def generate_review_comments(diff_text):
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
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        response_text = response.choices[0].message.content
        suggestions = json.loads(response_text)
        return suggestions
    except Exception as e:
        print("Error during OpenAI call or JSON parsing:", e)
        sys.exit(1)

def post_comment(file_path, line, body):
    comment_payload = {
        "body": body,
        "path": file_path,
        "line": line,
        "side": "RIGHT"
    }
    comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}/comments"
    response = requests.post(comments_url, headers=headers, json=comment_payload)
    if response.status_code not in [200, 201]:
        print(f"Failed to comment on {file_path}:{line} - {response.status_code}: {response.text}")
    else:
        print(f"Comment posted to {file_path}:{line}")

def main():
    print("Fetching diff...")
    diff = fetch_pr_diff()

    print("Generating review suggestions with GPT...")
    suggestions = generate_review_comments(diff)

    if not suggestions:
        print("No comments generated.")
        return

    print("Posting comments to GitHub...")
    for comment in suggestions:
        try:
            post_comment(comment["file"], comment["line"], comment["comment"])
        except KeyError:
            print("Invalid comment format:", comment)

if __name__ == "__main__":
    main()
