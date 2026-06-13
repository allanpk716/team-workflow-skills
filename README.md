# team-workflow-skills

一套 **Claude Code 技能（skills）**，为小团队构建 AI 驱动的 Gitea 协作工作流：把「口头描述需求 → 各自开发 → 线下验收」的原始流程，正规化为「需求细化 → 任务拆解 → 自动发布 Issue → 周验收简报」的闭环。

> 面向 7 人左右、前后端分离、使用 [Gitea](https://gitea.io) 自建仓库的团队。

## 工作流

```
            team-setup：一次性配置 tea CLI + 验收 Gitea 连通（前置）

  需求（口头 / 草稿）
    │  ① team-refine      AI 细化需求 → 标准需求文档
    ▼
    │  ② team-decompose   AI 拆解任务 → TL 分配 → 自动发布 Gitea Issue（含依赖）
    ▼
  团队认领开发（Git Flow：dev + issue-N-xxx 分支，PR 验收）
    │  ③ team-report      拉 Gitea 数据 → 周验收会简报
    ▼
```

## 四个技能

| 技能 | 作用 |
|------|------|
| `team-setup` | 一次性配置 tea CLI，连通并验收 Gitea |
| `team-refine` | PM 把粗糙需求细化为标准需求文档（AI 标注 `[推测]`/`[建议]`，PM 确认） |
| `team-decompose` | AI 把需求拆解为结构化任务，TL 审核分配，一键发布为 Gitea Issue（标签 / 里程碑 / 依赖自动建立） |
| `team-report` | 从 Gitea 拉本周 Issue / PR / 里程碑数据，生成周验收简报（成员工作量、依赖阻塞、未认领等信号） |

## 安装

```bash
# 1. clone
git clone https://github.com/allanpk716/team-workflow-skills.git

# 2. 把 4 个技能目录复制到 Claude Code skills 目录
cp -r team-workflow-skills/team-* ~/.claude/skills/
```

在 Claude Code 中即可通过 `/team-setup`、`/team-refine`、`/team-decompose`、`/team-report` 调用。

## 依赖与前置

- **Claude Code**（CLI / Desktop / IDE 插件）
- **Gitea** 实例（自建内网或公网均可）
- **tea CLI**（Gitea 官方 CLI），配置好 `tea login`
- **Python 3.7+**（运行发布 / 采集脚本）

## 配置

1. `tea login add --name <name> --url <your-gitea> --token <your-token>`，再 `tea logins default <name>`
2. 在 Claude Code 里 `/team-setup` 验收连通性
3. （可选）在项目 `CLAUDE.md` 写团队成员名单、Gitea 仓库地址，供 team-decompose / report 读取

## 已知注意事项

- **tea 的 POST 传参在 v0.12.0 有 bug**：发布 / 采集脚本一律用 urllib 直连 Gitea REST API，不依赖 tea 的写操作；tea 仅用于只读查询。
- **tea config 位置**：Windows 上 tea v0.12.0 把 config 存在 `%LOCALAPPDATA%\tea\config.yml`，脚本的 `load_config` 已覆盖 Linux / macOS / Windows（Roaming + Local）。
- **Issue 依赖**：用 Gitea 原生 dependencies API（body 为 `{index, owner, repo}`），可享受依赖 UI 与 block-closing。

## License

MIT — 见 [LICENSE](./LICENSE)。
