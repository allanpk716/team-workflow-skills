---
name: team-setup
description: 配置 Gitea CLI（tea）连通内网 Gitea 服务并验收可用。安装检测、登录配置、仓库验证、Issue 读写测试一站式完成。
---

<objective>
为团队开发工作流提供一次性环境配置和连通性验收。确保 tea CLI 已安装、已连接内网 Gitea、对目标仓库有读写权限，并能成功创建和关闭 Issue。

本技能是 team-* 系列技能的前置条件，必须在 team-decompose 之前执行。
</objective>

<quick_start>
**基本用法：**

```
/team-setup
```

或：

```
Use team-setup to configure Gitea CLI
```

技能会自动检测环境，逐步引导完成配置，最终输出验收报告。
</quick_start>

<workflow>
## 工作流

### Step 1：检测 tea CLI 安装

检查 `tea` 是否在 PATH 中：

```bash
tea --version
```

**如果未安装，提供安装指引：**

```bash
# 方式 1：Go install（需要 Go 环境）
go install code.gitea.io/tea@latest

# 方式 2：直接下载二进制
# 访问 https://gitea.com/gitea/tea/releases 下载对应平台的二进制
# Windows: tea-0.14.1-windows-amd64.exe → 重命名为 tea.exe 放入 PATH
# Linux:   tea-0.14.1-linux-amd64 → chmod +x → 放入 /usr/local/bin/
```

验证：
```bash
tea --version
# 期望输出类似：tea version 0.14.1
```

**版本要求：** >= 0.12.0（需要 `tea api` 和 JSON 输出支持）

### Step 2：检测已有登录配置

```bash
tea login list
```

如果有已配置的登录，展示列表供用户选择使用或重新配置。

### Step 3：配置 Gitea 连接（如需要）

向用户收集以下信息：

| 信息 | 说明 | 示例 |
|------|------|------|
| Gitea URL | 内网 Gitea 服务地址 | `https://gitea.company.local` |
| Access Token | 个人访问令牌 | 在 Gitea → Settings → Applications → Generate Token |
| 登录名称 | 本地别名 | `internal` |

执行配置：

```bash
tea login add \
  --name internal \
  --url https://gitea.company.local \
  --token YOUR_ACCESS_TOKEN
```

验证连接：
```bash
tea login default internal
tea whoami
# 期望输出当前登录用户信息
```

**获取 Access Token 的步骤（引导用户）：**

1. 登录 Gitea Web UI
2. 进入 Settings → Applications → Access Tokens
3. 点击 "Generate New Token"
4. Token 名称：`tea-cli`
5. 权限：至少勾选 `issue`、`repository`、`organization`（建议全选）
6. 复制生成的 Token（只显示一次）

### Step 4：检测当前仓库

```bash
git remote -v
```

从 remote URL 解析出 owner/repo，确认仓库关联到已配置的 Gitea。

如果不在 git 仓库中，或 remote 不指向 Gitea，提示用户：
- 进入项目目录后重试
- 或使用 `--repo owner/repo` 指定仓库

### Step 5：仓库权限验证

```bash
# 验证读取权限
tea issues list --repo {owner}/{repo} --limit 1

# 验证标签读取
tea labels list --repo {owner}/{repo}

# 验证里程碑读取
tea milestones list --repo {owner}/{repo}
```

如果任何命令失败，说明权限不足或仓库地址错误。

### Step 6：Issue 读写验收测试

创建一个测试 Issue，然后立即关闭它，验证完整的读写权限：

```bash
# 创建测试 Issue
tea issues create \
  --repo {owner}/{repo} \
  --title "[team-setup] 连通性测试" \
  --description "这是 team-setup 技能的自动化连通性测试，稍后会自动关闭。"

# 从输出解析 Issue 编号
# 假设为 #N

# 关闭测试 Issue
tea issues close {N} --repo {owner}/{repo}
```

### Step 7：输出验收报告

```
============================================
  Gitea CLI 配置验收报告
============================================

[✓] tea CLI 版本: 0.14.1
[✓] Gitea 连接: https://gitea.company.local
[✓] 登录用户: zhangsan
[✓] 仓库: myorg/my-project
[✓] Issue 读取: OK
[✓] Issue 写入: OK（测试 Issue #42 已创建并关闭）
[✓] 标签管理: OK
[✓] 里程碑管理: OK

配置状态: 通过 ✓
可以开始使用 /team-decompose

配置信息保存位置:
  tea 配置: ~/.config/tea/config (Linux/Mac)
            %APPDATA%\tea\config (Windows)
============================================
```

如果任何步骤失败，标记为 `[✗]` 并给出修复建议。
</workflow>

<prerequisites>
## 前提条件

- Git 已安装
- 有内网 Gitea 的账号
- 有目标仓库的写权限
- 网络 can reach Gitea 服务
</prerequisites>

<troubleshooting>
## 常见问题

**tea 未找到**
```bash
# 检查是否安装
which tea          # Linux/Mac
where tea          # Windows

# 如果安装了但不在 PATH 中，添加到 PATH
# Windows: 将 tea.exe 所在目录加入系统 PATH
# Linux/Mac: ln -s /path/to/tea /usr/local/bin/tea
```

**tea login add 失败：连接被拒绝**
- 检查 Gitea URL 是否正确（注意 http vs https）
- 检查网络是否可达：`curl https://gitea.company.local`
- 检查是否需要 VPN

**tea whoami 失败：认证错误**
- Token 可能已过期，重新生成
- 确认 Token 权限足够
- 确认 URL 和 Token 匹配同一个 Gitea 实例

**仓库权限不足**
- 确认 Gitea 账号有该仓库的写权限
- 检查 Token 的 repository 权限是否勾选
- 如果是组织仓库，确认组织成员身份

**Windows 上 tea 配置位置**
```
%APPDATA%\tea\config
# 通常在 C:\Users\{username}\AppData\Roaming\tea\config
```

**tea version 过低**
```bash
# 更新到最新版
go install code.gitea.io/tea@latest
# 或重新下载最新二进制
```
</troubleshooting>

<implementation>
## 实现指引

**当本技能被触发时，按以下步骤执行：**

1. **逐步检测**：依次执行 Step 1-7，每步检测通过才进入下一步
2. **交互式引导**：需要用户输入（Gitea URL、Token）时使用 AskUserQuestion
3. **实时反馈**：每步结果立即告知用户（通过/失败/跳过）
4. **错误恢复**：失败时给出明确修复建议，修复后可从失败步骤继续
5. **幂等安全**：验收测试创建的 Issue 会立即关闭，不影响项目

**验收测试的清理：**
- 创建的测试 Issue 必须关闭（不能删除，Gitea 不支持删除 Issue）
- Issue 标题包含 `[team-setup]` 前缀，便于识别
- 如果创建失败，不需要清理

**输出要求：**
- 最终必须输出完整的验收报告（Step 7 格式）
- 如果有失败项，报告末尾给出修复步骤摘要
- 通过后提示用户可以开始使用 `/team-decompose`
</implementation>

<configuration>
## 配置持久化

tea CLI 的登录配置会自动保存，无需额外配置文件。

**team-decompose 依赖的环境要求：**

| 项目 | 要求 | 验证命令 |
|------|------|---------|
| tea 版本 | >= 0.12.0 | `tea --version` |
| 登录状态 | 已配置且为默认 | `tea whoami` |
| 仓库访问 | 有写权限 | `tea issues list --repo {repo}` |

team-setup 验收通过 = team-decompose 可以正常工作。
</configuration>
