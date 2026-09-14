# Operit Virtual Screen Auto Skill

在 [Operit](https://github.com/AAswordman/Operit) 的**虚拟屏**上，用 UI 子代理安全操作手机 App（微信 / 美团 / 拼多多等）的标准化 Skill。

## ✨ 核心价值

- **点得准**：截图 + tesseract OCR + 画框校验，精确定位界面元素（解决子代理估坐标点歪的问题）
- **不重复找**：场景坐标数据库（SQLite 三表），命中即秒点，未命中走截图定位并自动补录
- **安全接管**：支付/密码等敏感环节 AI 停手，通知用户接管
- **结果直达**：查询类操作完成后，同时弹 Toast + 发系统通知

## 📦 目录结构

```
virtual_screen_auto/
├── SKILL.md                    # Skill 主文件（流程 + 约束 + 数据库说明）
└── scripts/
    ├── scene_db.py             # 场景坐标数据库（SQLite 三表结构）
    └── draw_by_ratio.py        # 按比例在截图上画框（校验用）
```

## 🗄️ 数据库设计（三表混合结构）

| 表 | 含义 | 唯一键 |
|---|---|---|
| `screens` | 界面（App + Activity） | `(package_name, activity)` |
| `elements` | 界面上的可点元素 + 比例坐标 | `(screen_id, label)` |
| `actions` | 一个操作 | `action_name` |
| `action_steps` | 操作的第 N 步 → 引用 [界面 + 元素] | — |

数据库文件（`data/scenes.db`）**不含在仓库中**（含本机个人场景数据）。
首次使用时脚本会自动创建空库。

## 🔧 前置条件

- Operit 已授予 **Shizuku** 权限
- 已启用「**实验性虚拟显示**」
- 「UI 控制器」功能模型支持**图片理解（多模态）**
- 环境装有 `tesseract`（含 `chi_sim`）与 Python3（自带 sqlite3）

## 🚀 快速开始

```bash
# 建库
python3 scripts/scene_db.py init

# 新增：界面 → 元素 → 操作
python3 scripts/scene_db.py add-screen  --app 拼多多 --pkg com.xunmeng.pinduoduo --act "首页"
python3 scripts/scene_db.py add-element --pkg com.xunmeng.pinduoduo --act "首页" --label "个人中心" --xy "901,983"
python3 scripts/scene_db.py add-action  --name "拼多多查物流" \
    --steps "com.xunmeng.pinduoduo|首页|个人中心; com.xunmeng.pinduoduo|个人中心页|待收货"

# 查询
python3 scripts/scene_db.py query-action --name "再来一单"
python3 scripts/scene_db.py query-screen --pkg com.xunmeng.pinduoduo --act "首页"
```

详见 [`SKILL.md`](virtual_screen_auto/SKILL.md)。

## 📄 License

MIT
