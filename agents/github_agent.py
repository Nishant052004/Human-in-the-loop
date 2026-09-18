import os
from github import Github

# Load environment variables from .env if present
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def get_repo_readme(repo_name):
    """Fetch README.md from target GitHub repository with authentication or unauthenticated fallback."""
    try:
        g = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()
        repo = g.get_repo(repo_name)
        file = repo.get_contents("README.md")
        content = file.decoded_content.decode()
        return content
    except Exception as e:
        raise RuntimeError(f"Unable to fetch README for '{repo_name}': {e}")