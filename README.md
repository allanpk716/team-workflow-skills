# team-workflow-skills

Claude Code 技能包——AI 驱动的 Gitea 团队协作工作流（需求细化 → 任务拆解发布 → 周报）。

> **给 AI agent**：本包安装 4 个 Claude Code 技能，安装后用 `/team-setup`、`/team-refine`、`/team-decompose`、`/team-report` 调用。
> **人类协作流程、角色分工、使用举例见 [WORKFLOW.md](./WORKFLOW.md)。**

## 这是什么

4 个技能组成闭环（面向 7 人左右、Gitea 自建、前后端分离的团队）：

| 技能 | 触发 | 作用 |
|------|------|------|
| `team-setup` | `/team-setup` | 一次性：配置 tea CLI + 验收 Gitea |
| `team-refine` | `/team-refine <原始需求>` | 粗糙/口头需求 → 标准需求文档（AI 标 `[推测]`/`[建议]`，PM 确认）|
| `team-decompose` | `/team-decompose <需求文档>` | AI 拆解 → TL 分配 → 自动发布 Gitea Issue（标签 / 里程碑 / 依赖）|
| `team-report` | `/team-report` | 拉 Gitea 周数据 → 周验收简报（完成率 / 成员工作量 / 阻塞 / 未认领）|

## 安装

```bash
git clone https://github.com/allanpk716/team-workflow-skills.git
cp -r team-workflow-skills/team-* ~/.claude/skills/
```

在 Claude Code 中按需调用：`/team-setup`（首次）→ `/team-refine` → `/team-decompose` → 每周 `/team-report`。

## 依赖

- **Claude Code**（CLI / Desktop / IDE 插件）
- **Gitea** 实例（自建）
- **tea CLI v0.12.0**（必须固定此版本，见下「须知」）
- **Python 3.7+**（运行发布 / 采集脚本）

## 配置

```bash
tea login add --name <name> --url <your-gitea> --token <your-token>
tea logins default <name>
```
然后 `/team-setup` 验收连通。可选：把团队成员名单 + Gitea 仓库写进项目 `CLAUDE.md`，供 decompose / report 读取。

## AI agent 须知

- **tea POST 在 v0.12.0 有 bug**：发布 / 采集脚本一律用 urllib 直连 Gitea REST API，不依赖 tea 写操作；tea 仅用于只读查询。
- **tea 版本必须固定 v0.12.0**：`@latest` 会拉到残缺的 v1.3.3，0.14.1/0.13.0 在 Win10 启动即 hang。
- **tea config 位置（Win）**：`%LOCALAPPDATA%\tea\config.yml`（Local 非 Roaming）；`load_config` 已覆盖 Linux / macOS / Windows。
- **Issue 依赖**：Gitea 原生 dependencies API，body 为 `{index, owner, repo}`。
- **publish-tasks.py 健壮性**：发布前拓扑排序检测循环依赖；assignee 不存在时先建 issue 再单独指派（不丢任务）。

## 文件结构

- `team-setup/` `team-refine/` `team-decompose/` `team-report/` — 4 个技能（各自的 `SKILL.md` + 脚本）
- [WORKFLOW.md](./WORKFLOW.md) — **人类协作工作流、角色分工、使用举例**
- [LICENSE](./LICENSE) — MIT
