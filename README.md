# AI Agent Skills & Plugins（多 Agent 共用仓库）

本仓库由**多个不同平台的 AI Agent 共同使用与维护**，每个 Agent 拥有自己独立的顶层目录。

## 📁 仓库目录结构

```
.
├── README.md              # 本文件（结构规范 + 协作流程）
├── .gitignore
│
├── operit/                # Operit 平台
│   ├── skills/
│   │   └── <skill_name>/
│   │       ├── SKILL.md           # 必须：Skill 主文件（含 frontmatter）
│   │       ├── scripts/           # 可选：附带脚本
│   │       └── data/              # 本地数据目录（.gitignore 已排除，不提交）
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

### 顶层目录一览

| 目录 | 归属平台 | 说明 |
|---|---|---|
| `operit/` | Operit | 虚拟屏自动化等 Skill |
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
5. 若需要新的顶层平台目录，请新建一个 `<platform>/` 并在此 README 的表格中补充说明。

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
- ✅ 先 **pull** 再改； ✅ 走 **分支 + PR**； ❌ 不要直接提交到 `main`。
- ✅ 一次 PR 只做一件相关的事，便于审核。
- ✅ 提交前确认没有把 `data/`、`*.db`、密钥等本地文件加入。

## 📄 License

除非各目录内另有说明，默认 MIT。
