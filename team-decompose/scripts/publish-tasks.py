#!/usr/bin/env python3
"""
team-decompose-publish.py
将 team-decompose 拆解的任务 JSON 批量发布到 Gitea（curl 直连 API，绕过 tea bug）

用法：
    python publish-tasks.py tasks.json [--repo owner/repo] [--token TOKEN] [--gitea URL] [--dry-run]
"""

import json
import subprocess
import sys
import os
import re
import urllib.request
import urllib.error


def load_config():
    """从 tea 配置或环境变量加载 gitea url 和 token"""
    config_paths = [
        os.path.expanduser("~/.config/tea/config.yml"),
        os.path.expandvars("%APPDATA%/tea/config.yml"),
        os.path.expandvars("%LOCALAPPDATA%/tea/config.yml"),  # tea v0.12.0 on Win10 实际位置
    ]
    url = os.environ.get("GITEA_URL")
    token = os.environ.get("GITEA_TOKEN")
    for p in config_paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            if not url:
                m = re.search(r"url:\s*(\S+)", txt)
                if m:
                    url = m.group(1)
            if not token:
                m = re.search(r"token:\s*(\S+)", txt)
                if m:
                    token = m.group(1)
    return url, token


def api(method, url, token, data=None):
    """调用 Gitea API，返回 (status_code, json_or_text)"""
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def parse_repo_from_git():
    out = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True).stdout
    m = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", out.strip())
    return m.group(1) if m else None


def ensure_labels(base, token, repo, dry_run):
    standard = {"backend": "5b9bd5", "frontend": "70ad47", "integration": "ffc000",
                "deploy": "ed7d31", "docs": "a5a5a5", "test": "9dc3e6",
                "priority:high": "ff0000", "priority:medium": "ff8c00", "priority:low": "008000"}
    if dry_run:
        print("  [DRY-RUN] labels:", ", ".join(standard)); return
    status, existing = api("GET", f"{base}/repos/{repo}/labels", token)
    names = {l["name"].lower() for l in existing} if isinstance(existing, list) else set()
    for name, color in standard.items():
        if name.lower() not in names:
            s, _ = api("POST", f"{base}/repos/{repo}/labels", token, {"name": name, "color": color})
            print(f"  label {name}: {'created' if s == 201 else 'exists/skip'}")


def build_body(task):
    b = task.get("body", {})
    lines = [f"## 目标\n{b.get('goal', task.get('title',''))}\n"]
    crit = b.get("acceptance_criteria", [])
    if crit:
        lines.append("## 验收标准")
        [lines.append(f"- [ ] {c}") for c in crit]
        lines.append("")
    if b.get("implementation_hints"):
        lines.append(f"## 实现提示\n{b['implementation_hints']}\n")
    lines.append(f"## 预估复杂度\n{task.get('complexity','medium')}（{b.get('estimated_effort','未知')}）\n")
    lines.append("---\n> 此 Issue 由 team-decompose 自动生成")
    return "\n".join(lines)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("tasks_file")
    p.add_argument("--repo")
    p.add_argument("--token")
    p.add_argument("--gitea")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    with open(args.tasks_file, encoding="utf-8") as f:
        data = json.load(f)

    repo = args.repo or parse_repo_from_git()
    cfg_url, cfg_tok = load_config()
    base = (args.gitea or cfg_url or "").rstrip("/")
    token = args.token or cfg_tok
    if not repo:
        print("[ERROR] 无 repo，用 --repo owner/repo 或在 git 仓库内运行"); sys.exit(1)
    if not base or not token:
        print("[ERROR] 无 gitea url/token，用 --gitea --token 或配置 tea"); sys.exit(1)

    base_api = f"{base}/api/v1"
    print(f"Repo: {repo} | API: {base_api} | Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}\n")

    print("=== Step 1: 标签 ===")
    ensure_labels(base_api, token, repo, args.dry_run)

    print("\n=== Step 2: 里程碑 ===")
    ms = data.get("milestone", {})
    ms_title = ms.get("title", "Untitled")
    ms_id = None
    if args.dry_run:
        print(f"  [DRY-RUN] milestone: {ms_title}")
    else:
        s, r = api("POST", f"{base_api}/repos/{repo}/milestones", token,
                   {"title": ms_title, "description": ms.get("description", "")})
        print(f"  milestone '{ms_title}': HTTP {s}")
        if s == 201 and isinstance(r, dict):
            ms_id = r.get("id")

    # 查 label 名称→ID 映射（Gitea 创建 Issue 的 labels 字段需要 ID）
    label_id = {}
    if not args.dry_run:
        s, r = api("GET", f"{base_api}/repos/{repo}/labels", token)
        if isinstance(r, list):
            label_id = {l["name"]: l["id"] for l in r}

    print(f"\n=== Step 3: 创建 {len(data.get('tasks',[]))} 个 Issue ===")
    tasks = data.get("tasks", [])
    issue_map = {}
    for i, t in enumerate(tasks):
        title = f"[{t.get('type','backend')}] {t.get('title','Untitled')}"
        body = build_body(t)
        if args.dry_run:
            print(f"  [{i+1}] {title} → {t.get('assignee') or 'unassigned'}"); continue
        want_labels = [t.get("type","backend"), f"priority:{t.get('priority','medium')}"]
        label_ids = [label_id[n] for n in want_labels if n in label_id]
        payload = {"title": title, "body": body,
                   "assignees": [t["assignee"]] if t.get("assignee") else []}
        if ms_id is not None:
            payload["milestone"] = ms_id
        if label_ids:
            payload["labels"] = label_ids
        s, r = api("POST", f"{base_api}/repos/{repo}/issues", token, payload)
        if s == 201 and isinstance(r, dict) and "number" in r:
            issue_map[i+1] = r["number"]
            print(f"  #{r['number']} {title}" + (f" → {t['assignee']}" if t.get('assignee') else ""))
        else:
            print(f"  [FAIL {s}] {title}: {str(r)[:100]}")

    if not args.dry_run:
        print(f"\n=== Step 4: 依赖回填 ===")
        # Gitea dependencies API body 是 IssueMeta {index, owner, repo}
        # （旧 {"new_dependency": N} 在 1.26.2 返回 404 "repository does not exist"）
        dep_owner, _, dep_repo = repo.partition("/")
        for i, t in enumerate(tasks):
            deps = t.get("dependencies", [])
            if not deps or (i+1) not in issue_map:
                continue
            for dep in deps:
                if dep in issue_map:
                    s, _ = api("POST", f"{base_api}/repos/{repo}/issues/{issue_map[i+1]}/dependencies", token,
                               {"index": issue_map[dep], "owner": dep_owner, "repo": dep_repo})
                    print(f"  #{issue_map[i+1]} depends #{issue_map[dep]}: HTTP {s}")

    print(f"\n{'='*50}\n完成: {len(issue_map)} issues | milestone: {ms_title}" +
          (f" | DRY-RUN" if args.dry_run else ""))


if __name__ == "__main__":
    main()
