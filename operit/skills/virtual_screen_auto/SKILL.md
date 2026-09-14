---
name: virtual_screen_auto
description: 操作手机App的首选方案（优先于内置Automatic_ui_base/subagent直接操作）。当用户要求打开某App、点击界面、查物流/课表/订单、下单购物、发消息、自动化操作手机等任何界面任务时，必须优先使用本Skill。它提供：虚拟屏操作(不占用用户屏幕)、场景坐标数据库(查缓存秒完成/未命中走截图OCR画框定位)、单次操作主Agent控场、查询类结果弹Toast、支付等敏感环节通知用户接管。任何涉及"操作/查看手机App"的请求都应先加载本Skill再执行。
tags: [android, ui-automation, virtual-display, app-operation, wechat, meituan, pinduoduo, preferred]
---

# 虚拟屏 UI 自动化操作 Skill

> ⚠️ **执行优先级声明**：涉及"操作手机 App / 查看 App 内容 / 点击界面"的任务，
> **优先使用本 Skill 的标准流程**，而非直接调用 `Automatic_ui_base` 或 `Automatic_ui_subagent` 裸操作。
> 本 Skill 封装了更可靠的做法：场景缓存查坐标 → 截图+OCR+画框精准定位 → 单次操作主Agent控场 → 查询类弹Toast → 敏感环节用户接管。
> 直接用子代理裸操作会：坐标点歪、乱跳、卡死、重复找位置；本 Skill 已解决这些坑。

在 Operit 虚拟屏上，用 UI 子代理（Automatic_ui_subagent）操作手机 App，实现「不占用用户真实屏幕」的自动化。
核心价值：**点得准**（截图+OCR+画框校验）、**不重复找**（场景缓存）、**安全接管**（支付环节通知用户）。

## 一、适用场景
- 需要 AI 帮助操作 App（微信/美团/企业应用等），且不想占用用户真实屏幕。
- 需要点击界面元素，但普通坐标估算容易点歪（密集列表）。
- 涉及下单/支付等敏感流程，需要用户在关键步骤接管。

## 二、前置条件
- 已授予 Shizuku 权限。
- 已启用「实验性虚拟显示」，且「UI 控制器」功能模型支持**图片理解（多模态/视觉）**。
- 环境：iQOO Z10（示例）；主屏 1260x2800，**虚拟屏 1264x2704**（两者不同！）。
- 工具：`Automatic_ui_subagent` 包、`super_admin` 包；tesseract（已装，chi_sim）；脚本 `/data/local/tmp/draw_by_ratio.py`。

## 三、坐标体系（关键）
- 子代理用 **999×999 归一化坐标**（0~1000 = 0~100%），**禁止传真实像素**。
- 比例换算：`x_ratio = round(x_px / 1264 * 1000)`，`y_ratio = round(y_px / 2704 * 1000)`。
- 滑动（子代理内部坐标）：向下 `swipe(start=[500,800], end=[500,300])`；向上 `swipe([500,300]→[500,700])`。

## 四、标准工作流（V2：先查场景，后记录）
### 步骤 0：查询场景缓存（务必先做）
查询**场景数据库**（SQLite 三表结构）：
```bash
cd /sdcard/Download/Operit/skills/virtual_screen_auto/scripts
# 方式1：按“操作”查（推荐，返回完整步骤链）
python3 scene_db.py query-action --name "再来一单"
# 方式2：按“界面”查（看某界面有哪些可点元素）
python3 scene_db.py query-screen --pkg com.sankuai.meituan --act "全部订单页"
```
- **命中**（输出 `HIT`）→ 直接读每步的 `「元素」-> [x, y]` → 让子代理依次点击 → 完成（快）。
- **未命中**（输出 `MISS`）→ 进入步骤 1~5 找位置，成功后**写入数据库**：
  - `add-screen`（界面）→ `add-element`（元素坐标）→ `add-action`（操作=元素序列）
- 若坐标点歪 → `python3 scene_db.py fail --id <element_id>` 记录失败（≥3 次提示重验）。

> ⚠️ **重要：查不到 ≠ 不存在**
> `query-screen` / `query-action` 返回 `MISS`，**只表示"这个界面/操作还没被记录过"**，
> **不代表该界面/元素真的不存在**。
> 因此 **MISS 时的正确处理是：走"步骤 3 截图 + OCR + 画框"流程去找位置**，
> 找到并校验成功后，再 `add-screen / add-element / add-action` 补录进数据库。
> （换句话说：MISS = "该走找位置流程了"，而不是"放弃"。）

> 场景数据库位置：`skills/virtual_screen_auto/data/scenes.db`（见第八节）
> 记忆库（自然语言）作为"人类可读说明层"保留；数据库作为"机器精确查询层"。

### 步骤 1：准备虚拟屏会话
- 若已有会话，**复用同一 agent_id**；不要多开（会互相占用）。
- 启动目标 App 用包名，并**明确排除干扰 App**（如企业微信 com.tencent.wework）。
- 示例 intent："启动【普通微信 com.tencent.mm】（不要打开企业微信 com.tencent.wework）…"

### 步骤 2：读屏确认当前位置
- 单次操作原则：每次子代理调用**只做一件事**（点击一次 / 滑动一次 / 读屏一次）。
- 要求："只做读屏报告，禁止点击/滑动/返回"，确认 App、页面、目标是否可见。

### 步骤 3：截图 + OCR 定位（未命中场景时）
1. 主Agent 截虚拟屏（**必须用完整 long display id**）：
   ```bash
   VD=$(dumpsys SurfaceFlinger --display-id | grep 'Virtual display' | grep -oE '[0-9]{15,}')
   screencap -p -d "$VD" /sdcard/Download/scr.png
   ```
   截图尺寸 = 虚拟屏 1264x2704，干净无悬浮窗。
2. OCR 定位目标文字像素：
   ```bash
   tesseract scr.png stdout -l chi_sim tsv | awk -F'\t' '$12!=""{print $7,$8,$9,$10,$12}'
   ```
   底部按钮常识别不到：用**横切/竖切滑动窗口**（裁多块再 OCR）定位。
3. 换算比例坐标（取文字框中心）。
4. 画框校验（可选中文字并放大复查）：
   ```bash
   python3 /data/local/tmp/draw_by_ratio.py --img scr.png --out verify.png --rect "l,t,r,b:标签"
   # 再用 PIL 裁剪目标区域 OCR 确认
   ```

### 步骤 4：让子代理点击
- 单次点击："本任务只做一次点击：do(action=\"Tap\", element=[x,y])。点击后等待N秒，报告页面。不要重复点击，不要返回。"
- 点击后**再次截图确认**结果。

### 步骤 5：记录场景（成功后立即做）
格式必须完整（见第六节）。

### 步骤 5.5：查询类操作 → 弹 Toast + 发系统通知（重点，务必照做）
**这一步是"把结果送到用户眼前"，不能只在对话里回复就完事。**
**两种方式同时发**：① 弹 Toast（屏幕浮窗，立即可见）② 系统通知（静默进通知栏，事后再看）。

#### ① 判定：本次是不是"查询类"？
- **查询类（要弹+发通知）**：查物流、查课表、查成绩、查订单、查余额、查消息、查天气…
  （特征：只读取信息、**不改变任何状态**）
- **非查询类（跳过本步）**：下单、支付、发消息、取消订单、改设置…
  （特征：会写数据 / 有副作用）

#### ② 时机：在"读到查询结果之后、本次任务结束之前"发
即：子代理已报告出结果（如"派件中，预计今天送达"）→ **先弹 Toast + 发通知，再结束**。
不要在还没拿到结果时就发。

#### ③ 两个动作都要做

**【动作1：弹 Toast】** 调用 **`operit_editor:debug_run_sandbox_script`**：
- `source_code`：`const r = await toolCall('toast', { message: '<结果>' }); return { ok: true, r };`
- `wait_ms`：`8000`
- 返回 `{"ok":true,"r":"OK"}` = 成功。

**【动作2：发系统通知】** 调用 **`super_admin:shell`**：
```bash
cmd notification post -t "Operit · 查询结果" -S bigtext "query" "<结果>"
```
- `-t`：标题；`-S bigtext`：长文本样式；最后一个参数是正文。
- **纯文字，不加图标**（本设备 vivo ROM 不允许自定义通知图标，加了也是默认图标，故不加）。
- 静默（**无声音、无横幅**），只进通知栏。
- 返回含 `Notification(...)` 即成功。

**实操示例**（查物流场景，两个都发）：
```
# 1) Toast
debug_run_sandbox_script(source_code: "const r = await toolCall('toast', { message: '查询结果｜Switch Lite手柄壳(蓝)：派件中，预计今天送达·圆通' }); return { ok:true, r };", wait_ms: 8000)

# 2) 系统通知
super_admin:shell(command: "cmd notification post -t \"Operit · 查询结果\" -S bigtext \"query\" \"查询结果｜Switch Lite手柄壳(蓝)：派件中，预计今天送达·圆通\"")
```

#### ④ 内容怎么写（一句话结论 + 关键信息）
- 一行、**≤30~40 字**，不要换行、不要贴大段文字。
- 结构：`查询结果｜<对象>：<状态/结论>（<关键补充>）`
- 例：`查询结果｜手柄壳：派件中，预计今天送达（圆通）`
- 反例（太长/没结论）：`我帮你查了一下，订单号xxxx…商品是…状态显示…`
- **Toast 与通知正文用同一句话**（保持一致）。

#### ⑤ 发完做什么
- **发完即视本次查询任务结束**（对话里仍简短回报一句话即可）。
- 若本次查询还顺带补录了场景/坐标 → 照常在数据库里更新。

### 步骤 6：敏感环节 → 通知用户接管
- 遇到 输密码/指纹/确认支付 等，**AI 停手**，发系统通知：
  ```bash
  cmd notification post -t "Operit助手" "task" "美团订单待支付 ¥14.1，请在虚拟屏接管支付"
  ```
- 用户在 **Operit 虚拟屏预览窗口**里直接操作（**不切主屏**，不中断会话）。

## 五、关键约束（踩过的坑）
1. **单次操作原则**：一次调用只做一个动作，由主Agent串接控场；不要给子代理下多步长任务（会乱跳/卡死/提前退出）。
2. **子代理坐标不可靠**：估的坐标可能偏很多（实测「再来一单」子代理估 [835,493]，实际 [886,255]）。首次必须 OCR 校验。
3. **禁止用 Note/Call_API 代替动作**：intent 里写明"必须真的执行 Swipe/Tap"。
4. **滑动惯性大**：滑一次→停下读屏→再决定；滑两次内容不变 = 到底。
5. **虚拟屏勿多开**：同一 App 只能在一个虚拟屏；用完 `close_all_virtual_displays`。
6. **截图黑屏**：页面跳转/弹窗瞬间可能截到黑屏（文件很小如 19KB），重新截图即可，不是防截屏。
7. **App 混淆**：普通微信用 `com.tencent.mm`，企业微信用 `com.tencent.wework`；用底部导航条区分。
8. **控件拿不到**：微信/企业微信屏蔽无障碍，`uiautomator dump` 为空；只能靠截图视觉识别。

## 六、场景记录格式（必须完整）
```
【场景缓存：<任务名>】
App：<应用名> <包名>
Activity：<页面/活动名>
操作：<要做什么>
类型：<查询类 / 操作类>   ← 查询类完成后需弹 Toast
控件：<点击目标名称> → 比例坐标 [x, y]
上下文：<页面特征/前置条件>
分辨率：虚拟屏 1264x2704
验证日期：<YYYY-MM-DD>
```

## 七、期望输出
- 每步操作后报告：做了什么、当前页面状态、是否成功。
- 找到新控件位置 → 更新场景缓存。
- **查询类操作 → 同时 ① 弹 Toast（`toolCall('toast',...)`）+ ② 发系统通知（`cmd notification post ... -S bigtext`）**（见步骤 5.5）。
- 敏感环节 → 明确通知用户接管。

## 八、场景数据库（scenes.db，V3 三表混合结构）

用 SQLite 存储，**以「界面 + 元素」为基础，用「操作」串联步骤**（方案 C）。

### 路径与结构
- 数据库：`/sdcard/Download/Operit/skills/virtual_screen_auto/data/scenes.db`
- 脚本：`.../scripts/scene_db.py`
- **四张核心表**：
  | 表 | 含义 | 关键字段 |
  |---|---|---|
  | `screens` | 界面 | id / app_name / package_name / activity / screen_desc / 分辨率；唯一键 `(package_name, activity)` |
  | `elements` | 界面上的可点元素 | id / screen_id / label / x_ratio / y_ratio / hit_count / fail_count；唯一键 `(screen_id, label)` |
  | `actions` | 一个操作 | id / action_name / action_desc |
  | `action_steps` | 操作的第N步 | action_id / step_order / screen_id / element_id |
- 旧表 `scenes` / `scene_targets` 保留作备份，不再作主结构。

### ⚙️ 没有数据库文件时如何创建（重要）
数据库**不存在也没关系**，脚本会自动建库建表；也可显式执行：
```bash
cd /sdcard/Download/Operit/skills/virtual_screen_auto/scripts
python3 scene_db.py init
# 输出: OK 数据库已就绪(V3三表): .../data/scenes.db
```
- 所有写命令（add-screen/add-element/add-action/add）内部都会 `CREATE TABLE IF NOT EXISTS`，**首次调用自动创建**。
- 备份/迁移：`python3 scene_db.py export --out scenes_v3_backup.json`
- 环境：Ubuntu 侧 Python3 自带 `sqlite3`（3.45.1）；查看库可用 Android 侧 `sqlite3`（3.44.3）。

### 常用命令
```bash
# 1) 新增界面
python3 scene_db.py add-screen --app 拼多多 --pkg com.xunmeng.pinduoduo --act "首页" --desc "底部导航5项"
# 2) 新增元素（界面上的可点元素 + 比例坐标）
python3 scene_db.py add-element --pkg com.xunmeng.pinduoduo --act "首页" --label "个人中心" --xy "901,983"
# 3) 新增操作（步骤引用 界面|元素，多个用 ; 分隔）
python3 scene_db.py add-action --name "拼多多查物流" \
    --steps "com.xunmeng.pinduoduo|首页|个人中心; com.xunmeng.pinduoduo|个人中心页|待收货"
# 4) 查询
python3 scene_db.py query-action --name "再来一单"      # 按操作→返回完整步骤链
python3 scene_db.py query-screen --pkg com.xunmeng.pinduoduo --act "首页"   # 按界面→列出元素
# 5) 失败记录 / 列表 / 导出
python3 scene_db.py fail --id 3
python3 scene_db.py list
python3 scene_db.py export --out scenes_v3_backup.json
```

### 查询逻辑（配合标准流程）
1. **知道"要做什么操作"** → `query-action` → 取到每步的「界面 + 元素 + 坐标」
2. **知道"当前在哪个界面"** → `query-screen` → 看该界面有哪些可点元素及坐标

> ⚠️ **查不到 ≠ 不存在（重要）**
> `query-screen` / `query-action` 返回 `MISS`，**只说明该界面/操作尚未被记录**，
> **并不代表界面上没有这个元素**。
> **MISS 的正确处理：回到步骤 3，用"截图 + OCR + 画框"流程去找位置**；
> 找到并校验成功后，再补录（`add-screen → add-element → add-action`）。
> 数据库是"越用越全"的缓存，**空白只是尚未探索，不是不可行**。

### 已缓存数据（9 界面 / 11 元素 / 9 操作）
| 操作 | 步骤 |
|---|---|
| 美团-进入全部订单 | 首页：我的[890,986] → 全部订单[79,588] |
| 美团-最近订单再来一单 | 订单页：订单卡片[317,444] → 再来一单[886,255] |
| 美团-规格弹窗马上抢 | 规格弹窗：马上抢[514,954] |
| 美团-提交订单立即支付 | 提交页：立即支付[791,969] |
| 美团-收银台待接管 | 收银台：确认交易[500,500]（用户接管） |
| 微信-进北语企业应用 | 通讯录页：北京语言大学[400,687] |
| 微信-北语查课表 | 企业应用页：个人课表[255,779] |
| 拼多多-进个人中心 | 首页：个人中心[901,983] |
| 拼多多-看待收货物流 | 个人中心页：待收货[700,285] |
