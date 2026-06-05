import requests, base64, os, json, subprocess, sys, tempfile, mimetypes

TOKEN = "your_github_pat_here"
OWNER = "wasiliakimumw-sudo"
REPO = "nkulawua---app"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"

repo_dir = r"D:\Mantchombe websites\nkula_wua-main"

# Patterns to exclude
exclude_patterns = [
    ".git", "__pycache__", "venv", ".env", "db.sqlite3", "*.pyc",
    ".DS_Store", "*.zip", "*.log", "node_modules", ".gitignore",
    "seed_data.json", "check_pg_data.py", "reset_pg.py", "seed_pg.py",
    "full_seed_pg.py", "load_pg.py", "push_via_api.py",
    "STATICFILES_DIRS", "djang-project-production.zip", "wsgi_pythonanywhere.py"
]

import fnmatch
def should_exclude(path):
    rel = os.path.relpath(path, repo_dir)
    parts = rel.replace("\\", "/").split("/")
    for p in parts:
        for pat in exclude_patterns:
            if fnmatch.fnmatch(p, pat):
                return True
    return False

# Collect files
files = []
for root, dirs, filenames in os.walk(repo_dir):
    dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
    for f in filenames:
        fp = os.path.join(root, f)
        if not should_exclude(fp):
            rel_path = os.path.relpath(fp, repo_dir).replace("\\", "/")
            files.append((rel_path, fp))

print(f"Found {len(files)} files to push")

# Get latest commit on remote
r = requests.get(f"{BASE}/git/ref/heads/main", headers=HEADERS)
if r.status_code == 200:
    latest_commit_sha = r.json()["object"]["sha"]
    print(f"Latest commit: {latest_commit_sha}")
    # Get the tree SHA from the latest commit
    r2 = requests.get(f"{BASE}/git/commits/{latest_commit_sha}", headers=HEADERS)
    base_tree_sha = r2.json()["tree"]["sha"]
    print(f"Base tree: {base_tree_sha}")
else:
    print(f"No existing commits, starting fresh")
    latest_commit_sha = None
    base_tree_sha = None

# Create blobs for each file
tree_items = []
for rel_path, abs_path in files:
    try:
        with open(abs_path, "rb") as f:
            content = f.read()
        
        # For text files, use base64 encoded content
        # For binary files, use base64 encoded content
        encoded = base64.b64encode(content).decode()
        
        # Determine if it's text or binary
        is_text = True
        try:
            content.decode("utf-8")
        except:
            is_text = False
        
        mode = "100755" if os.access(abs_path, os.X_OK) else "100644"
        
        tree_items.append({
            "path": rel_path,
            "mode": mode,
            "type": "blob",
            "content": content.decode("utf-8", errors="replace") if is_text else encoded
        })
        print(f"  Added: {rel_path} ({len(content)} bytes)")
    except Exception as e:
        print(f"  Error reading {rel_path}: {e}")

# Create tree
print("\nCreating tree...")
# GitHub API has a 7MB limit for the tree creation via content-based blobs
# Let's create blobs individually for larger files
blob_items = []
for item in tree_items:
    if len(item.get("content", "")) > 100000:  # large files
        print(f"  Creating blob for large file: {item['path']}")
        r = requests.post(f"{BASE}/git/blobs", headers=HEADERS, json={
            "content": item["content"],
            "encoding": "base64" if len(item["content"]) != len(item["content"].encode("utf-8")) else "utf-8"
        })
        if r.status_code == 201:
            blob_items.append({
                "path": item["path"],
                "mode": item["mode"],
                "type": "blob",
                "sha": r.json()["sha"]
            })
        else:
            print(f"  ERROR creating blob: {r.status_code} {r.text}")
    elif len(item.get("content", "")) > 0:
        blob_items.append(item)
    else:
        blob_items.append({
            "path": item["path"],
            "mode": item["mode"],
            "type": "blob",
            "content": item.get("content", "")
        })

# Create tree
r = requests.post(f"{BASE}/git/trees", headers=HEADERS, json={
    "base_tree": base_tree_sha,
    "tree": blob_items
})

if r.status_code == 201:
    new_tree_sha = r.json()["sha"]
    print(f"Tree created: {new_tree_sha}")
else:
    print(f"ERROR creating tree: {r.status_code} {r.text}")
    sys.exit(1)

# Get author info
r = requests.get(f"{BASE}/git/commits/{latest_commit_sha}", headers=HEADERS) if latest_commit_sha else None
author = {"name": "nkula", "email": "nkula@users.noreply.github.com"}

# Create commit
commit_data = {
    "message": "Deploy nkula_wua accounting system",
    "tree": new_tree_sha,
    "parents": [latest_commit_sha] if latest_commit_sha else [],
    "author": author,
    "committer": author
}

print("\nCreating commit...")
r = requests.post(f"{BASE}/git/commits", headers=HEADERS, json=commit_data)
if r.status_code == 201:
    new_commit_sha = r.json()["sha"]
    print(f"Commit created: {new_commit_sha}")
else:
    print(f"ERROR creating commit: {r.status_code} {r.text}")
    # Try with minimal content
    if "content" in str(r.text):
        print("Retrying with blob SHA approach...")
        sys.exit(1)
    sys.exit(1)

# Update ref
print("\nUpdating main branch...")
r = requests.patch(f"{BASE}/git/refs/heads/main", headers=HEADERS, json={
    "sha": new_commit_sha,
    "force": True
})
if r.status_code == 200:
    print(f"SUCCESS! Branch updated to {new_commit_sha}")
else:
    print(f"ERROR: {r.status_code} {r.text}")
