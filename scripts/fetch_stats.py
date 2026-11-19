"""Collect profile numbers from the GitHub API (runs inside GitHub Actions).

usage: python scripts/fetch_stats.py [github-username]
needs: $GITHUB_TOKEN (the workflow's built-in token is enough -> public data only)
writes: data/stats.json
"""
import datetime as dt
import json
import os
import pathlib
import sys

import requests

OUT = pathlib.Path(__file__).parent.parent / "data" / "stats.json"
API = "https://api.github.com"


def session():
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-bot"})
    if os.environ.get("GITHUB_TOKEN"):
        s.headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return s


def repos(s, user):
    out, page = [], 1
    while True:
        r = s.get(f"{API}/users/{user}/repos", params={"per_page": 100, "page": page, "type": "owner"}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def languages(s, repo_list):
    total = {}
    for repo in repo_list:
        if repo.get("fork"):
            continue
        r = s.get(repo["languages_url"], timeout=30)
        if r.ok:
            for name, n in r.json().items():
                total[name] = total.get(name, 0) + n
    grand = sum(total.values()) or 1
    ranked = sorted(total.items(), key=lambda kv: -kv[1])
    return [{"name": k, "bytes": v, "pct": round(100 * v / grand, 1)} for k, v in ranked]


def contributions(s, user, created: dt.datetime):
    """Commits / PRs / issues per calendar year via GraphQL (public contributions)."""
    now = dt.datetime.now(dt.timezone.utc)
    iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
    frag = "contributionsCollection(from:\"%s\",to:\"%s\"){totalCommitContributions totalPullRequestContributions totalIssueContributions}"
    aliases = []
    for y in range(created.year, now.year + 1):
        start = dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc)
        end = min(dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        aliases.append(f"y{y}:" + frag % (iso(start), iso(end)))
    aliases.append("last:" + frag % (iso(now - dt.timedelta(days=364)), iso(now)))
    q = '{user(login:"%s"){%s}}' % (user, " ".join(aliases))
    r = s.post(f"{API}/graphql", json={"query": q}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    u = data["data"]["user"]
    years = [v for k, v in u.items() if k.startswith("y")]
    return {
        "commits_total": sum(y["totalCommitContributions"] for y in years),
        "pull_requests": sum(y["totalPullRequestContributions"] for y in years),
        "issues": sum(y["totalIssueContributions"] for y in years),
        "commits_year": u["last"]["totalCommitContributions"],
    }


def collect(user):
    s = session()
    u = s.get(f"{API}/users/{user}", timeout=30)
    u.raise_for_status()
    u = u.json()
    rs = repos(s, user)
    own = [r for r in rs if not r.get("fork")]
    stats = {
        "user": user,
        "public_repos": u["public_repos"],
        "own_repos": len(own),
        "stars": sum(r["stargazers_count"] for r in own),
        "forks": sum(r["forks_count"] for r in own),
        "languages": languages(s, rs),
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    created = dt.datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
    try:
        stats.update(contributions(s, user, created))
    except Exception as e:  # keep the rest of the card useful if GraphQL is refused
        print("contribution counts unavailable:", e, file=sys.stderr)
    return stats


if __name__ == "__main__":
    user = (sys.argv[1] if len(sys.argv) > 1 else None) or os.environ.get("GITHUB_USER") \
        or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not user:
        raise SystemExit("pass a GitHub username (arg or $GITHUB_USER)")
    OUT.parent.mkdir(exist_ok=True)
    data = collect(user)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{user}: {data['public_repos']} repos, {len(data['languages'])} languages, commits={data.get('commits_total')}")
