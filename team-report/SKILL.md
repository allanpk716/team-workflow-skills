---
name: team-report
description: 生成团队周验收会进度简报。从 Gitea 拉取本周 Issue/PR 数据，按里程碑和成员统计进度，输出会议用的结构化简报。
---

<objective>
为每周的验收会自动生成进度简报，省去人工"汇报进度"环节，让会议聚焦于演示和讨论。

从 Gitea 拉取本周数据，按里程碑、成员、状态维度统计，输出一份结构化的会议简报。
</objective>

<quick_start>
**基本用法：**

```
/team-report
```

或指定时间范围：

```
/team-report --week 2026-W24
/team-report --from 2026-06-06 --to 2026-06-13
```

**前提条件：**
- team-setup 已通过验收（tea CLI 已配置）
- 当前仓库关联到 Gitea

**输出：** 一份周报简报（Markdown），可直接用于会议投屏或发送到团队群。
</quick_start>

<workflow>
## 工作流

### Step 1：确定时间范围

默认取**本周一到当前日期**。

- `--week YYYY-WNN`：指定 ISO 周（如 2026-W24）
- `--from YYYY-MM-DD --to YYYY-MM-DD`：自定义范围
- 无参数：本周一至今

### Step 2：拉取 Gitea 数据

从当前仓库拉取：

```bash
# 仓库地址
REPO=$(解析自 git remote)

# 1. 本周关闭的 Issue（已完成的任务）
tea issues list --repo $REPO --state closed --date-from {from} --fields index,title,assignees,milestone,labels,closed --output json

# 2. 当前打开的 Issue（进行中/待办）
tea issues list --repo $REPO --state open --fields index,title,assignees,milestone,labels,created --output json

# 3. 本周合并的 PR
tea pulls list --repo $REPO --state closed --fields index,title,author,merged --output json

# 4. 里程碑列表
tea milestones list --repo $REPO --fields title,state,closed,open --output json
```

### Step 3：数据统计与分析

按以下维度分析：

**里程碑维度：**
- 各里程碑完成率 = closed_issues / (open_issues + closed_issues)
- 本周关闭的 Issue 所属里程碑

**成员维度：**
- 各成员本周完成的 Issue 数
- 各成员当前进行中的 Issue
- 各成员待办（未开始的 open issue）

**状态维度：**
- 本周新增 Issue 数
- 本周关闭 Issue 数
- 本周合并 PR 数
- 阻塞任务（有依赖未完成 / 长时间未更新）

**质量信号：**
- 长时间未更新的 open issue（可能阻塞）
- 有依赖但依赖未完成的 issue
- 本周创建但无人认领的 issue

### Step 4：生成简报

按 weekly_report_template 生成 Markdown 简报。

### Step 5：输出

- 显示简报内容
- 询问是否保存为文件（默认 `docs/reports/weekly-{YYYY-MM-DD}.md`）
- 提示会议要点
</workflow>

<weekly_report_template>
## 周报简报模板

```markdown
# 团队周报 - {YYYY年MM月DD日}

## 📊 本周概况

| 指标 | 数值 |
|------|------|
| 新增任务 | {N} |
| 完成任务 | {N} |
| 进行中 | {N} |
| 合并 PR | {N} |
| 完成率 | {N}% |

## 🏆 里程碑进度

### {里程碑1} - {完成率}%
- 完成: {closed}/{total}
- 剩余: {open} 个任务
- 预计完成: {deadline 或 未知}

### {里程碑2} - {完成率}%
...

## 👥 成员工作量

| 成员 | 本周完成 | 进行中 | 状态 |
|------|---------|--------|------|
| {成员1} | {N} | {N} | ✅ 正常 |
| {成员2} | {N} | {N} | ⚠️ 负载高 |

> 待办（未指派任务）不进成员表，由下方「未认领任务」承载。

## ✅ 本周完成（{N}项）

| # | Issue | 标题 | 负责人 | 里程碑 |
|---|-------|------|--------|--------|
| {num} | #{id} | {title} | {assignee} | {milestone} |

## 🔄 进行中（{N}项）

| # | Issue | 标题 | 负责人 | 状态说明 |
|---|-------|------|--------|---------|
| {num} | #{id} | {title} | {assignee} | {进度/阻塞} |

## 🔀 本周合并的 PR（{N}个）

| PR | 标题 | 作者 | 关联 Issue |
|----|------|------|-----------|
| #{id} | {title} | {author} | #{issue} |

## ⚠️ 需要关注

### 依赖阻塞（依赖了未完成的任务，数据来自 Gitea 原生 dependencies）
- #{id} {title} ← 被 #{blocked_by} {blocked_by_title} 阻塞

### 长时间未更新（>7天无进展）
- #{id} {title} - 最后更新 {date}

### 未认领任务
- #{id} {title} - 创建于 {date}，无人认领

## 📝 会议讨论要点建议

1. **{里程碑1}** 进度是否需要调整？
2. **{阻塞项}** 需要谁协助？
3. 下周重点：{基于剩余任务建议}

---
*由 team-report 自动生成 | 数据来源：Gitea*
```
</weekly_report_template>

<data_collection>
## 数据收集脚本

使用 `scripts/collect-weekly-data.py` 批量拉取 Gitea 数据并输出 JSON：

```bash
python ~/.claude/skills/team-report/scripts/collect-weekly-data.py \
  --repo owner/repo \
  --from 2026-06-06 \
  --to 2026-06-13
```

输出结构化 JSON，包含：
- `closed_issues`: 本周关闭的 Issue
- `open_issues`: 当前打开的 Issue
- `merged_prs`: 本周合并的 PR
- `milestones`: 里程碑进度

脚本会处理分页、日期过滤、JSON 解析，避免在技能流程中多次调用 tea。
</data_collection>

<implementation>
## 实现指引

**当本技能被触发时，按以下步骤执行：**

1. **解析参数**：确定时间范围（默认本周一至今）

2. **检测环境**：
   - 确认 tea 已配置（`tea whoami`）
   - 从 git remote 解析 owner/repo
   - 如未配置，提示先运行 `/team-setup`

3. **拉取数据**：
   - 优先使用 `scripts/collect-weekly-data.py` 批量拉取
   - 脚本不可用时回退到逐个 tea 命令

4. **分析数据**：
   - 计算各维度统计
   - 识别阻塞和风险
   - 生成成员工作量分布

5. **生成简报**：
   - 按 weekly_report_template 填充
   - 重点突出"需要关注"的部分
   - 给出会议讨论建议

6. **输出与保存**：
   - 显示简报
   - 询问是否保存到 `docs/reports/weekly-{date}.md`
   - 提示会议主持人重点关注的 2-3 个问题

**关键原则：**
- **数据驱动**：所有数字必须来自 Gitea，不编造
- **突出风险**：阻塞、长时间未更新、负载不均要醒目标记
- **可执行**：会议讨论建议要具体，不是泛泛而谈
- **简洁**：会议前 1 分钟能看完，避免信息过载
</implementation>

<output_handling>
## 输出处理

**默认输出到对话**，便于会议投屏。

**保存为文件**（可选）：
```
docs/reports/weekly-{YYYY-MM-DD}.md
```

**会议使用建议：**
1. 会前 10 分钟生成并发到团队群
2. 会议开始投屏展示简报
3. 跳过"汇报进度"环节，直接进入演示和讨论
4. 会后将会议决定追加到简报末尾
</output_handling>

<configuration>
## 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `team-report.members` | 自动从 Issue assignees 收集 | 团队成员名单（用于完整的工作量表） |
| `team-report.stale-days` | 7 | 多少天未更新标记为"长时间未更新" |
| `team-report.report-dir` | `docs/reports/` | 简报保存目录 |

**在 CLAUDE.md 中配置：**

```markdown
## team-report 配置
- 团队成员：张三, 李四, 王五, 赵六, 钱七, 孙八, 周九
- 阻塞阈值：5 天未更新
```
</configuration>
