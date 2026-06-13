#!/usr/bin/env python3
"""
collect-weekly-data.py
直连 Gitea REST API 批量拉取本周 Issue/PR/Milestone 数据，输出结构化 JSON 供 team-report 使用。

为什么不用 tea：tea v0.12.0 的 --output json 是给人看的扁平格式，缺 closed_at/updated_at/
assignees 字段，导致周报的核心统计（本周关闭、成员工作量、本周合并 PR）全部落空。
故改为 urllib 直连 Gitea API（与 publish-tasks.py 同款，已验证）。

用法：
    python collect-weekly-data.py --repo owner/repo                       # 默认本周一至今
    python collect-weekly-data.py --repo owner/repo --week 2026-W24
    python collect-weekly-data.py --repo owner/repo --from 2026-06-06 --to 2026-06-13
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta


def load_config():
    """从 tea 配置或环境变量加载 gitea url 和 token（与 publish-tasks.py 一致）"""
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


def api_get(base_api, token, path, params=None):
    """GET Gitea API 单页，返回 JSON"""
    q = ""
    if params:
        q = "?" + "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_api}{path}{q}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:200]
        print(f"[ERROR] GET {url} -> {e.code}: {body}", file=sys.stderr)
        raise


def api_get_paged(base_api, token, path, extra=None, page_size=50):
    """分页 GET，合并所有页（Gitea 单页上限 50）。404 视为该资源在此仓库不可用（如空仓库无 PR），返回空列表。"""
    results, page = [], 1
    while True:
        params = {"page": page, "limit": page_size}
        if extra:
            params.update(extra)
        try:
            batch = api_get(base_api, token, path, params)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  [WARN] {path} -> 404（仓库可能无此资源，按空处理）", file=sys.stderr)
                return []
            raise
        if not batch:
            break
        results.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return results


def iso_week_range(iso_week_str):
    """2026-W24 -> (monday, sunday)"""
    year, week = iso_week_str.split("-W")
    monday = datetime.strptime(f"{year}-{week}-1", "%G-W%V-%u").date()
    return monday, monday + timedelta(days=6)


def default_this_week():
    """本周一到今天"""
    today = datetime.now().date()
    return today - timedelta(days=today.weekday()), today


def _in_range(dt_str, from_date, to_date):
    if not dt_str:
        return False
    return str(from_date) <= dt_str[:10] <= str(to_date)


def _parse_date(dt_str):
    """'2026-06-13T16:30:05+08:00' -> date（忽略时区，仓库内统一时区即可）"""
    return datetime.strptime(dt_str[:19], "%Y-%m-%dT%H:%M:%S").date()


def collect(base_api, token, repo, from_date, to_date, stale_days=7):
    print(f"Collecting {repo} ({from_date} -> {to_date})", file=sys.stderr)

    # 1. 本周关闭的 Issue（按 closed_at 过滤；Gitea 的 since 按 updated_at，无法精确按 closed_at）
    print("  closed issues...", file=sys.stderr)
    all_closed = api_get_paged(base_api, token, f"/repos/{repo}/issues",
                               {"state": "closed", "type": "issues"})
    closed_issues = [i for i in all_closed
                     if _in_range(i.get("closed_at"), from_date, to_date)]

    # 2. 当前打开的 Issue
    print("  open issues...", file=sys.stderr)
    open_issues = api_get_paged(base_api, token, f"/repos/{repo}/issues",
                                {"state": "open", "type": "issues"})

    # 3. 本周合并的 PR（按 merged_at 过滤）
    print("  merged PRs...", file=sys.stderr)
    all_prs = api_get_paged(base_api, token, f"/repos/{repo}/pulls", {"state": "closed"})
    merged_prs = [p for p in all_prs
                  if p.get("merged_at") and _in_range(p["merged_at"], from_date, to_date)]

    # 4. 里程碑（含 open_issues/closed_issues 计数，供完成率计算）
    print("  milestones...", file=sys.stderr)
    milestones = api_get_paged(base_api, token, f"/repos/{repo}/milestones")

    # 本周新增（created_at 在范围内的 issue，closed+open 去重）
    seen = set()
    new_issues = 0
    for i in closed_issues + open_issues:
        if i.get("number") in seen:
            continue
        seen.add(i.get("number"))
        if _in_range(i.get("created_at"), from_date, to_date):
            new_issues += 1

    # ---- 成员工作量 ----
    member_stats = {}
    all_members = set()

    def tally(name, key):
        if not name or name == "null":
            return
        all_members.add(name)
        member_stats.setdefault(name, {"completed": 0, "in_progress": 0})
        member_stats[name][key] += 1

    for i in closed_issues:
        for a in (i.get("assignees") or []):
            tally(a.get("login"), "completed")
    for i in open_issues:  # 已指派但未关闭 = 进行中
        for a in (i.get("assignees") or []):
            tally(a.get("login"), "in_progress")

    # ---- 质量信号：长时间未更新 / 未认领 / 依赖阻塞 ----
    print("  risk signals...", file=sys.stderr)
    today = datetime.now().date()
    open_nums = {i.get("number") for i in open_issues}
    stale, unassigned, blocked = [], [], []
    for i in open_issues:
        num = i.get("number")
        title = i.get("title", "")
        upd = i.get("updated_at")
        if upd:
            age = (today - _parse_date(upd)).days
            if age > stale_days:
                stale.append({"number": num, "title": title,
                              "updated_at": upd, "days_idle": age})
        if not (i.get("assignees") or []):
            unassigned.append({"number": num, "title": title,
                               "created_at": (i.get("created_at") or "")[:10]})
        # 依赖阻塞：依赖了仍未完成的 issue
        deps = api_get_paged(base_api, token, f"/repos/{repo}/issues/{num}/dependencies")
        for d in deps:
            if d.get("number") in open_nums:
                blocked.append({"number": num, "title": title,
                                "blocked_by": d.get("number"),
                                "blocked_by_title": d.get("title", "")})
                break

    return {
        "repo": repo,
        "period": {"from": str(from_date), "to": str(to_date)},
        "summary": {
            "new_issues": new_issues,
            "closed_issues": len(closed_issues),
            "open_issues": len(open_issues),
            "merged_prs": len(merged_prs),
            "milestones": len(milestones),
        },
        "closed_issues": closed_issues,
        "open_issues": open_issues,
        "merged_prs": merged_prs,
        "milestones": milestones,
        "member_stats": member_stats,
        "all_members": sorted(all_members),
        "risk_signals": {"stale": stale, "unassigned": unassigned, "blocked": blocked},
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Collect weekly Gitea data for team-report")
    p.add_argument("--repo", required=True, help="owner/repo")
    p.add_argument("--gitea", help="Gitea base URL (默认: 从 tea config / 环境变量)")
    p.add_argument("--token", help="API token (默认: 从 tea config / 环境变量)")
    p.add_argument("--stale-days", type=int, default=7, help="未更新阈值（默认 7 天）")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--week", help="ISO 周，如 2026-W24")
    g.add_argument("--from", dest="from_date", help="起始日期 YYYY-MM-DD")
    p.add_argument("--to", dest="to_date", help="结束日期 YYYY-MM-DD")
    args = p.parse_args()

    if args.week:
        from_date, to_date = iso_week_range(args.week)
    elif args.from_date:
        from_date, to_date = args.from_date, (args.to_date or args.from_date)
    else:
        from_date, to_date = default_this_week()

    cfg_url, cfg_tok = load_config()
    base = (args.gitea or cfg_url or "").rstrip("/")
    base_api = f"{base}/api/v1"
    token = args.token or cfg_tok
    if not base or not token:
        print("[ERROR] 缺 gitea url/token，用 --gitea --token 或配置 tea config.yml",
              file=sys.stderr)
        sys.exit(1)

    result = collect(base_api, token, args.repo, from_date, to_date, args.stale_days)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
