
import os
import json
import time
import base64
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

BASE_URL = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

CATEGORIES = {
    "web_development": "topic:web-development",
    "mobile_development": "topic:mobile",
    "ai_machine_learning": "topic:machine-learning",
    "backend_development": "topic:backend",
    "developer_tools": "topic:developer-tools",
}

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def search_repositories(query, per_page=20):

    url = f"{BASE_URL}/search/repositories"

    params = {
        "q": f"{query} fork:false archived:false",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json().get("items", [])


def get_readme(full_name):

    url = f"{BASE_URL}/repos/{full_name}/readme"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code == 404:
        return ""

    response.raise_for_status()

    content = response.json().get("content", "")
    encoding = response.json().get("encoding", "")

    if encoding == "base64":
        decoded = base64.b64decode(content).decode(
            "utf-8", errors="replace"
        )
        return decoded

    return ""


def collect_repositories():

    repositories = {}
    
    for category, query in CATEGORIES.items():
        print(f"\nCollecting: {category}")

        try:
            items = search_repositories(query)

            for item in items:
                full_name = item["full_name"]

                if full_name in repositories:
                    continue

                print(f"Fetching README: {full_name}")

                try:
                    readme = get_readme(full_name)
                except requests.RequestException as error:
                    print(f"README error for {full_name}: {error}")
                    readme = ""

                repositories[full_name] = {
                    "id": item["id"],
                    "name": item["name"],
                    "full_name": full_name,
                    "description": item["description"],
                    "readme": readme,
                    "language": item["language"],
                    "topics": item.get("topics", []),
                    "stars": item["stargazers_count"],
                    "url": item["html_url"],
                    "category": category,
                }

                time.sleep(0.2)

        except requests.RequestException as error:
            print(f"Collection error for {category}: {error}")

    output_file = OUTPUT_DIR / "repositories.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            list(repositories.values()),
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nCollection completed!")
    print(f"Total repositories: {len(repositories)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    collect_repositories()
