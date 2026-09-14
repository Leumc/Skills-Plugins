# AI Agent Skills & Plugins

一个由**多个平台 AI Agent 共同维护**的能力仓库，收集整理各平台的 **Skill（技能）** 与 **Plugin（插件）**。

每个平台拥有独立的顶层目录，内容互不干扰；所有更新通过 Pull Request 审核合并。

## 📦 收录内容

### Operit

<table>
<tr><td width="30%"><b>virtual_screen_auto</b></td><td>

在 Operit **虚拟屏**上安全操作手机 App（微信 / 美团 / 拼多多等）的自动化 Skill。

- **点得准**：截图 + OCR + 画框校验，精确定位界面元素（解决普通坐标估算点歪的问题）
- **不重复找**：场景坐标数据库（SQLite），命中即秒点，未命中自动截图定位并补录
- **安全接管**：支付 / 密码等敏感环节 AI 停手，通知用户接管
- **结果直达**：查询类操作完成后，同时弹 Toast + 发系统通知

路径：`operit/skills/virtual_screen_auto/`
</td></tr>
</table>

### Codex

_暂无收录。_

### DeepSeek Harness

_暂无收录。_

### Hermes

_暂无收录。_

## 📁 目录结构

```
.
├── README.md              # 本文件
├── specification.md       # 目录结构规范 + 协作更新流程
├── operit/                # Operit 平台
│   ├── skills/
│   └── plugins/
├── codex/                 # Codex 平台
├── deepseek_harness/      # DeepSeek Harness
└── hermes/                # Hermes
```

各平台目录下的具体组织方式（`skills/<name>/SKILL.md`、`plugins/...`）与命名规则，见 [specification.md](specification.md)。

## 🤝 如何贡献 / 更新

本仓库**禁止直接提交到主分支**，所有改动需走分支 + **PR（Pull Request）** 流程。

完整的目录规范与更新步骤（拉取 → 建分支 → 修改 → 提交 PR）请阅读 **[specification.md](specification.md)**。

## 📄 License

除非各目录内另有说明，默认 MIT。
