# AI Agent Skills & Plugins

多平台 AI Agent 共用的能力仓库，收集各平台的 **Skill** 与 **Plugin**，通过 Pull Request 审核合并。

## 📦 Skills

### virtual_screen_auto（Operit）

在 Operit **虚拟屏**上安全操作手机 App（微信 / 美团 / 拼多多等）的自动化技能。

- **点得准**：截图 + OCR + 画框校验，精确定位界面元素，避免坐标估算点歪
- **不重复找**：场景坐标数据库，命中即秒点；未命中自动截图定位并补录
- **安全接管**：支付 / 密码等敏感环节 AI 停手，通知用户接管
- **结果直达**：查询类操作完成后，同时弹 Toast + 发系统通知

> 路径：`operit/skills/virtual_screen_auto/`

## 🤝 贡献

本仓库禁止直接提交到主分支，所有改动需走分支 + **PR（Pull Request）** 流程。

目录规范与更新步骤见 [specification.md](specification.md)。

## 📄 License

除非另有说明，默认 MIT。
