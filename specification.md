# 仓库规范（Specification）

本文件定义本仓库的**目录结构规范**与**协作更新流程**，供所有使用本仓库的 AI Agent 遵守。

## 📁 仓库目录结构

```
.
├── README.md              # 仓库说明（对外展示）
├── specification.md       # 本文件（结构与更新规范）
├── .gitignore
│
├── operit/                # Operit 平台
│   ├── skills/
│   │   └── <skill_name>/
│   │       ├── SKILL.md           # 必须：Skill 主文件（含 frontmatter）
│   │       ├── scripts/           # 可选：附带脚本
│   │       └── data/              # 本地数据目录（.gitignore 已排除，不提交）
│   ├── descriptions/              # Skill 描述文件（外置，不属于 Skill 本体）
│   │   └── <skill_name>.md
│   ├── assist_app/                # Operit 专用辅助组件 App 源码（原生 Android 能力补充）
│   │   ├── README.md              # 必须：该 App 的详细说明
│   │   ├── app/                   # Android 模块（源码 / 资源 / Manifest）
│   │   ├── gradle/                # Gradle Wrapper 与依赖版本目录
│   │   └── setup_android_env.sh   # ARM64 环境初始化脚本
│   └── plugins/
│       └── <plugin_name>/
│
├── codex/                 # Codex 平台
│   ├── skills/
│   └── plugins/
│
├── deepseek_harness/      # DeepSeek Harness
│   ├── skills/
│   └── plugins/
│
└── hermes/                # Hermes
    ├── skills/
    └── plugins/
```

### 目录一览

| 目录 | 归属平台 | 说明 |
|---|---|---|
| `operit/` | Operit | 虚拟屏自动化等 Skill |
| `operit/assist_app/` | Operit | Operit 专用辅助组件 App 源码（原生 Android 能力补充，如通知投递） |
| `codex/` | Codex | Codex 平台内容 |
| `deepseek_harness/` | DeepSeek Harness | Harness 平台内容 |
| `hermes/` | Hermes | Hermes 平台内容 |

## 📝 每个 Agent 如何建立自己的部分

1. **只在属于你的顶层目录内工作**，不要改动其他 Agent 的目录。
2. 在你的顶层目录下按需创建：
   ```
   <你的平台>/
     skills/<skill_name>/SKILL.md
     skills/<skill_name>/scripts/...   （可选）
     plugins/<plugin_name>/...          （可选）
   ```
3. **Skill 命名**：用小写字母 + 下划线（如 `virtual_screen_auto`），避免与其他 Skill 重名。
4. **不提交本地数据**：数据库、缓存、截图、密钥等一律不入库
   （根 `.gitignore` 已排除 `*.db`、`*_backup.json`、`*.png/jpg/log`、`__pycache__` 等）。
5. 若需要新的顶层平台目录，请新建一个 `<platform>/` 并在此文件的表格中补充说明。

## 🗂️ Skill 描述外置（重要约束）

> **Skill 的详细介绍不写在 README 里**，而是**单独建描述文件**，README 仅做索引。
> 目的：README 保持简洁；Skill 增多时不会臃肿。

规定：
1. 描述文件放在 **`<平台>/descriptions/<skill_name>.md`**。
   - 该目录**不属于 Skill 本体**，是额外目录，**不要放进 `skills/<skill_name>/` 里面**。
2. 描述文件可包含：功能介绍、核心能力、适用场景、前置条件、目录结构、路径等。
3. **README 中只放一行索引**，链接指向描述文件，例如：
   ```markdown
   - **[virtual_screen_auto](operit/descriptions/virtual_screen_auto.md)**（Operit）— 一句话说明
   ```
   （用列表，不用表格，避免被顶高）
4. 新增 / 修改 Skill 时：
   - 改 `<平台>/skills/<skill_name>/`（实现）
   - 同步改 `<平台>/descriptions/<skill_name>.md`（描述）
   - 在 README 索引表中维护对应行

## 🤝 更新流程（重要：直接提交会被禁用）

> ⚠️ **本仓库禁止直接 push 到主分支。** 所有更新必须走 **PR（Pull Request）** 流程。

标准步骤：

```bash
# 1) 拉取最新（务必先同步，避免冲突）
git checkout main
git pull origin main

# 2) 新建分支（分支名自取，建议带平台前缀）
git checkout -b <platform>/<change-desc>
#   例：git checkout -b operit/add-virtual-screen-auto

# 3) 在你的目录内修改 / 新增内容
git add <你的目录>
git commit -m "<platform>: <简述改动>"

# 4) 推送到远程分支
git push origin <platform>/<change-desc>

# 5) 在 GitHub 上创建 Pull Request
#    - base: main
#    - compare: 你刚推的分支
#    - 填写改动说明，等待审核合并
```

要点：
- ✅ 先 **pull** 再改； ✅ 走 **分支 + PR**； ❌ 不要直接提交到主分支。
- ✅ 一次 PR 只做一件相关的事，便于审核。
- ✅ 提交前确认没有把 `data/`、`*.db`、密钥等本地文件加入。

### ⚠️ PR 正文写法（避免 `\n` 变字面量）

**不要**把带 `\n` 的字符串内联传给 `--body`——shell 不会把 `\n` 转成换行，
结果 GitHub 上会显示成一坨带反斜杠的文本。

**正确做法：正文写入文件，用 `--body-file` 传。**

```bash
cat > /tmp/pr_body.md << 'EOF'
## 本次改动

### 新增
- `operit/skills/<name>/`：说明

### 说明
- 要点一
- 要点二
EOF

gh pr create --base master --head <你的分支> \
  --title "<类型>(<平台>): 简述" \
  --body-file /tmp/pr_body.md
```

- ✅ Markdown 正常渲染（标题、列表、代码块）
- ✅ 无 shell 转义坑
- 🔁 修改已有 PR 正文：`gh pr edit <PR号> --body-file /tmp/pr_body.md`
