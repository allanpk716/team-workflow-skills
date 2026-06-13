---
name: team-decompose
description: AI 驱动的需求任务拆解与 Gitea Issue 发布。PM 输入需求描述，AI 拆解为结构化任务，TL 审核并分配，一键发布到 Gitea。
---

<objective>
将软件开发需求拆解为结构化的开发任务，经团队负责人（TL）审核和分配后，通过 Gitea CLI（tea）发布为 Issue，供团队成员认领开发。

本技能是团队开发工作流的核心环节，衔接需求细化和开发执行。
</objective>

<quick_start>
**基本用法：**

```
/team-decompose 需求描述或需求文档路径
```

或：

```
Use team-decompose to decompose: [需求描述]
```

**示例：**

```
/team-decompose 用户管理模块：需要实现用户的注册、登录、角色分配。注册需要邮箱验证。角色分管理员和普通用户。前后端分离，后端提供 REST API，前端用 Vue 做页面。
```

**前提条件：**
- Gitea 实例已部署且可访问
- tea CLI 已安装并配置（`tea login` 已完成）
- 当前 git 仓库已关联 Gitea 远程仓库

**检查环境：**
```bash
tea --version
tea login list
git remote -v
```
</quick_start>

<roles>
## 角色定义

| 角色 | 在本技能中的职责 |
|------|----------------|
| **PM（项目经理）** | 提供需求描述，触发任务拆解，初审任务列表 |
| **TL（团队负责人）** | 审核任务技术可行性，决定任务分配，批准发布 |
| **AI（Claude）** | 执行任务拆解，生成结构化输出，执行发布脚本 |

PM 和 TL 可以是同一个人，技能流程不变。
</roles>

<workflow>
## 工作流

### Phase 1：需求分析

1. 读取用户输入的需求描述（直接文本或指向文件路径）
2. 如果输入是文件路径，读取文件内容
3. 分析需求，确认以下要素：
   - 项目背景与目标
   - 功能清单（做什么）
   - 验收标准（做到什么程度）
   - 技术约束（前后端分离、框架、语言等）
4. 如果信息不足，向用户提问补充（最多 2 轮）

### Phase 2：任务拆解

根据需求生成结构化任务列表。拆解原则：

**拆解粒度：**
- 每个任务应是一个开发者可在 1-3 天内完成的工作单元
- 按技术模块拆分，不按开发步骤拆分（"实现用户注册 API" 而非 "写代码 → 写测试 → 写文档"）
- 前后端分离的项目必须明确区分前端/后端/联调任务

**任务分类标签：**

| 标签 | 含义 |
|------|------|
| `backend` | 后端开发任务 |
| `frontend` | 前端开发任务 |
| `integration` | 前后端联调任务 |
| `deploy` | 部署/运维任务 |
| `docs` | 文档任务 |
| `test` | 测试任务 |

**优先级：**

| 优先级 | 含义 |
|--------|------|
| `high` | 核心功能，阻塞其他任务 |
| `medium` | 重要但非阻塞 |
| `low` | 锦上添花，可延后 |

**依赖关系：**
- 明确标注任务间的依赖（如 "联调任务依赖后端 API 完成"）
- 依赖使用任务序号引用（如 `depends: [1, 2]`）

### Phase 3：输出与审核

将拆解结果以表格形式展示给用户：

```
## 任务拆解结果

**Milestone：** [需求名称]
**截止日期：** [用户指定或留空]

| # | 标题 | 类型 | 优先级 | 依赖 | 预估复杂度 |
|---|------|------|--------|------|-----------|
| 1 | xxx | backend | high | - | 中 |
| 2 | xxx | frontend | high | 1 | 高 |
```

然后逐项展示每个任务的详细描述，供用户审核。

**审核交互：**
- 询问用户是否需要调整（增删改任务、调整依赖、修改描述）
- 用户确认后，进入分配环节

### Phase 4：任务分配

提示 TL 为每个任务指定负责人：

```
## 任务分配

请为以下任务指定负责人（输入团队成员名称，留空表示待分配）：

1. [后端] 设计用户表结构与数据库迁移 → ?
2. [后端] 注册 API（含邮箱验证） → ?
3. [前端] 登录/注册页面 → ?
...
```

TL 可以：
- 逐个指定负责人
- 使用"同上"快速填充
- 留空表示稍后分配
- 批量分配（如"张三负责所有 backend 任务"）

### Phase 5：发布到 Gitea

确认分配后，自动执行发布流程：

1. **创建标签**（如果不存在）：`backend`、`frontend`、`integration`、`deploy`、`docs`、`test`
2. **创建 Milestone**：以需求名称命名，设置截止日期
3. **批量创建 Issue**：
   - 标题：`[类型] 任务标题`
   - 描述：按 Issue 描述模板填充
   - 标签：任务类型 + 优先级
   - 里程碑：当前 Milestone
   - 指派人：TL 分配的负责人
4. **回填依赖关系**：在描述中追加 `Depends: #N, #M`
5. **输出发布结果摘要**

### Phase 6：确认

展示发布结果：

```
## 发布完成

Milestone: 用户管理模块
Issue 数量: 7

| # | Issue | 标题 | 负责人 | 链接 |
|---|-------|------|--------|------|
| 1 | #12 | [后端] 设计用户表结构 | 张三 | https://... |
| 2 | #13 | [后端] 注册 API | 张三 | https://... |
| ... |
```
</workflow>

<task_schema>
## 任务 JSON Schema

AI 拆解输出的每个任务必须符合以下结构：

```json
{
  "milestone": {
    "title": "需求/功能模块名称",
    "description": "一段话概述这个里程碑要达成什么",
    "deadline": "YYYY-MM-DD 或 null"
  },
  "tasks": [
    {
      "title": "实现用户注册 API",
      "type": "backend",
      "priority": "high",
      "complexity": "medium",
      "dependencies": [],
      "assignee": null,
      "body": {
        "goal": "一句话说明这个任务要达成什么",
        "acceptance_criteria": [
          "验收条件 1",
          "验收条件 2"
        ],
        "implementation_hints": "技术建议、参考方案、注意事项",
        "estimated_effort": "1-2天"
      }
    }
  ]
}
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | 是 | 简明任务标题，不超过 50 字 |
| `type` | 是 | `backend` / `frontend` / `integration` / `deploy` / `docs` / `test` |
| `priority` | 是 | `high` / `medium` / `low` |
| `complexity` | 是 | `low` / `medium` / `high` |
| `dependencies` | 是 | 依赖的任务序号列表（从 1 开始），无依赖为 `[]` |
| `assignee` | 否 | 负责人名称，初始为 null，由 TL 分配后填入 |
| `body.goal` | 是 | 任务目标 |
| `body.acceptance_criteria` | 是 | 验收条件列表，至少 2 条 |
| `body.implementation_hints` | 否 | 技术建议 |
| `body.estimated_effort` | 是 | 预估工时 |
</task_schema>

<issue_template>
## Gitea Issue 描述模板

每个发布的 Issue 描述格式：

```markdown
## 目标
{goal}

## 验收标准
- [ ] {acceptance_criteria[0]}
- [ ] {acceptance_criteria[1]}
...

## 实现提示
{implementation_hints}

## 依赖
{Depends: #N, #M 或 "无"}

## 预估复杂度
{complexity}（预估 {estimated_effort}）

---
> 此 Issue 由 team-decompose 技能自动生成，如需调整请直接编辑。
```
</issue_template>

<publish_commands>
## Gitea 发布命令参考

### 前置检查

```bash
# 检查 tea 是否安装
tea --version

# 检查登录状态
tea login list

# 检查当前仓库
git remote -v
```

### 创建标签（如果不存在）

```bash
# 检查现有标签
tea labels list --repo <owner>/<repo>

# 创建标准标签（如果不存在）
tea labels create --repo <owner>/<repo> --name "backend" --color "#5b9bd5"
tea labels create --repo <owner>/<repo> --name "frontend" --color "#70ad47"
tea labels create --repo <owner>/<repo> --name "integration" --color "#ffc000"
tea labels create --repo <owner>/<repo> --name "deploy" --color "#ed7d31"
tea labels create --repo <owner>/<repo> --name "docs" --color "#a5a5a5"
tea labels create --repo <owner>/<repo> --name "test" --color "#9dc3e6"

# 优先级标签
tea labels create --repo <owner>/<repo> --name "priority:high" --color "#ff0000"
tea labels create --repo <owner>/<repo> --name "priority:medium" --color "#ff8c00"
tea labels create --repo <owner>/<repo> --name "priority:low" --color "#008000"
```

### 创建 Milestone

```bash
tea milestones create \
  --repo <owner>/<repo> \
  --title "{milestone_title}" \
  --description "{milestone_description}" \
  --deadline {deadline}
```

### 创建 Issue

```bash
# 将 Issue 描述写入临时文件（避免 shell 转义问题）
cat > /tmp/issue-body-{N}.md << 'ISSUE_EOF'
{issue_body_content}
ISSUE_EOF

# 创建 Issue
tea issues create \
  --repo <owner>/<repo> \
  --title "[{type}] {title}" \
  --description "$(cat /tmp/issue-body-{N}.md)" \
  --labels "{type},priority:{priority}" \
  --milestone "{milestone_title}" \
  --assignees "{assignee}"
```

### 回填依赖关系

创建完所有 Issue 后，获取 Issue 编号，更新描述追加依赖：

```bash
# 追加依赖信息到描述
tea issues edit {issue_number} \
  --repo <owner>/<repo> \
  --description-append "Depends: #{dep1}, #{dep2}"
```

**注意：** `--description-append` 不是 tea 原生 flag，需要先读取现有描述再整体更新：

```bash
# 方案：使用 tea api 更新
tea api --method PATCH \
  repos/{owner}/{repo}/issues/{number} \
  -d body="$(cat /tmp/updated-body.md)"
```
</publish_commands>

<implementation>
## 实现指引

**当本技能被触发时，按以下步骤执行：**

### Step 1：解析输入

- 提取用户提供的需要求描述（直接文本或文件路径）
- 如果参数为空，提示用户输入需求描述

### Step 2：分析需求

- 理解需求的技术领域（前端/后端/全栈/其他）
- 识别技术约束（语言、框架、部署环境）
- 如果关键信息缺失，向用户提问（最多 2 轮，每轮不超过 3 个问题）

### Step 3：生成任务列表

- 按 task_schema 生成完整的 JSON 结构
- 确保每个任务粒度合适（1-3 天工作量）
- 确保依赖关系合理（无循环依赖）
- 确保前后端分离的项目有明确的联调任务

### Step 4：展示与审核

- 用表格形式展示任务总览
- 逐个展示任务详情
- 询问用户是否需要调整
- 根据用户反馈修改任务列表

### Step 5：任务分配

- 展示任务列表，请 TL 指定每个任务的负责人
- 接受各种分配格式（逐个/批量/部分跳过）
- 更新任务 JSON 中的 assignee 字段

### Step 6：发布到 Gitea

1. 从 `git remote -v` 获取仓库地址，解析出 owner/repo
2. 执行标签检查和创建
3. 创建 Milestone
4. 逐个创建 Issue（使用 Bash 工具执行 tea 命令）
5. 收集创建结果中的 Issue 编号
6. 回填依赖关系到 Issue 描述
7. 展示发布结果摘要

**错误处理：**
- tea 未安装：提示安装命令 `go install code.gitea.io/tea@latest`
- 未登录：提示 `tea login add`
- 仓库未关联：提示用户指定 `--repo` 参数
- Issue 创建失败：记录失败项，继续创建其余 Issue，最后汇总报告
- 标签已存在：忽略创建错误，继续流程
</implementation>

<configuration>
## 配置项

以下配置可通过项目 CLAUDE.md 或 .claude/settings.json 自定义：

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `team-decompose.repo` | 自动检测 | Gitea 仓库地址（owner/repo），留空则从 git remote 自动获取 |
| `team-decompose.gitea-url` | 自动检测 | Gitea 实例 URL，留空则从 tea login 配置获取 |
| `team-decompose.default-labels` | 标准六类 | 自定义任务类型标签 |
| `team-decompose.issue-prefix` | `[{type}]` | Issue 标题前缀格式 |
| `team-decompose.auto-publish` | `false` | 审核后是否自动发布（不询问确认） |

**在 CLAUDE.md 中配置示例：**

```markdown
## team-decompose 配置
- Gitea 仓库：myorg/my-project
- 团队成员：张三(后端), 李四(前端), 王五(全栈), 赵六(前端)
```
</configuration>

<examples>
## 使用示例

**示例 1：基本用法**

输入：
```
/team-decompose 用户管理模块：需要实现用户的注册、登录、角色分配。前后端分离。
```

**示例 2：从文件读取需求**

输入：
```
/team-decompose docs/requirements/user-auth.md
```

**示例 3：指定仓库**

输入：
```
/team-decompose --repo myorg/my-project 实现数据导出功能，支持 CSV 和 Excel 格式
```
</examples>

<troubleshooting>
## 常见问题

**tea 命令未找到**
```bash
# 安装 tea CLI
go install code.gitea.io/tea@latest
# 或从 https://gitea.com/gitea/tea/releases 下载二进制
```

**tea 未登录**
```bash
tea login add \
  --name my-gitea \
  --url https://gitea.example.com \
  --token YOUR_ACCESS_TOKEN
```

**创建 Issue 时标签不存在**
技能会自动检查并创建标准标签，如果创建失败可手动创建：
```bash
tea labels create --name "backend" --color "#5b9bd5"
```

**批量创建 Issue 速度慢**
tea CLI 逐个创建，20 个任务约需 30-60 秒。如果速度不可接受，可以使用 `tea api` 直接批量 POST。

**依赖回填失败**
依赖信息使用 `tea api` 更新 Issue body，确保 tea 版本 >= 0.12.0：
```bash
tea --version  # 需要 >= 0.12.0
```
</troubleshooting>
