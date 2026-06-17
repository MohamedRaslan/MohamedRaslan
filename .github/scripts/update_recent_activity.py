import json
import os
import re
import urllib.request


USERNAME = os.environ.get("PROFILE_USER", "MohamedRaslan")
README = "readme.md"
START = "<!--RECENT_ACTIVITY:start-->"
END = "<!--RECENT_ACTIVITY:end-->"


def fetch_events():
    url = f"https://api.github.com/users/{USERNAME}/events/public"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "User-Agent": "profile-readme-updater",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def describe_event(event):
    event_type = event.get("type", "")
    repo = event.get("repo", {}).get("name", "")
    payload = event.get("payload", {})

    if not repo:
        return None

    repo_link = f"https://github.com/{repo}"
    repo_md = f"[{repo}]({repo_link})"

    if event_type == "PushEvent":
        commits = payload.get("commits", [])
        count = len(commits)
        label = "commit" if count == 1 else "commits"
        return f"Pushed {count} {label} to {repo_md}"

    if event_type == "CreateEvent":
        ref_type = payload.get("ref_type", "item")
        return f"Created {ref_type} in {repo_md}"

    if event_type == "PullRequestEvent":
        action = payload.get("action", "updated")
        number = payload.get("pull_request", {}).get("number")
        suffix = f" #{number}" if number else ""
        return f"{action.title()} pull request{suffix} in {repo_md}"

    if event_type == "IssuesEvent":
        action = payload.get("action", "updated")
        number = payload.get("issue", {}).get("number")
        suffix = f" #{number}" if number else ""
        return f"{action.title()} issue{suffix} in {repo_md}"

    if event_type == "WatchEvent":
        return f"Starred {repo_md}"

    if event_type == "ForkEvent":
        return f"Forked {repo_md}"

    return None


def build_activity(events):
    items = []
    seen = set()
    for event in events:
        description = describe_event(event)
        if not description or description in seen:
            continue
        seen.add(description)
        items.append(f"- {description}")
        if len(items) == 5:
            break

    if not items:
        return "- Recent public activity will appear here after the workflow runs."

    return "\n".join(items)


def update_readme(activity):
    with open(README, "r", encoding="utf-8") as file:
        content = file.read()

    pattern = re.compile(f"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    replacement = f"{START}\n{activity}\n{END}"
    updated = pattern.sub(replacement, content)

    if updated != content:
        with open(README, "w", encoding="utf-8", newline="\n") as file:
            file.write(updated)


if __name__ == "__main__":
    update_readme(build_activity(fetch_events()))
