---
name: virtual_screen_auto
description: 操作手机App的唯一标准方案。当用户要求打开某App、点击界面、查物流/课表/订单、下单购物、发消息、自动化操作手机等任何界面任务时，必须使用本Skill。核心铁律：① 严禁让子代理自己猜坐标去点，坐标必须由主Agent先"截图+OCR+画框校验"得出；② 命中场景数据库才可直接点，未命中必须先截图定位再补录；③ 场景数据库可随时查（query-screen按界面查元素 / query-action按操作查链路），每进入新界面都应先查库、命中即用坐标省掉截图。它提供：虚拟屏操作(不占用用户屏幕)、场景坐标数据库、单次操作主Agent控场、查询类结果弹Toast、支付等敏感环节通知用户接管。
tags: [android, ui-automation, virtual-display, app-operation, wechat, meituan, pinduoduo, preferred]
---

# 虚拟屏 UI 自动化操作 Skill

## 🚫 四条铁律（违反即失败，必须遵守）

> **铁律 1 · 坐标只能"量"不能"猜"**
> **严禁**让 UI 子代理自己估算 / 猜坐标去点击。
> 任何一次点击前，坐标**必须**由主 Agent 通过「**截图 → OCR → 画框校验**」得出（或来自场景数据库）。
> 直接把点击目标交给子代理"看着点"是**明令禁止**的——它估的坐标会严重偏差（实测偏 100~200px）。

> **铁律 2 · 未命中数据库 ≠ 可以乱点**
> 场景数据库没有记录时，**必须**走「步骤 3 截图+OCR+画框定位」流程，
> **不允许**跳过定位、直接让子代理自己找位置/自己点。
> 定位成功后再补录进数据库。

> **铁律 3 · 子代理只当"手"，不当"眼"也不会"想"**
> 子代理每次**只执行一个明确动作**（点 [x,y] / 滑动一次 / 读屏报告），
> 坐标由主 Agent 决定。**禁止**给它下"帮我找到xx并点击"这类需要它自己判断位置的任务。

> **铁律 4 · 先查库，再动手**
> 场景数据库**可以随时查、应该随时查**（不是只在开头查一次）。
> 每进入一个新界面 / 每开始一个子任务 / 每不确定某元素在哪 → **先查库**：
> `query-screen`（按界面查元素）+ `query-action`（按操作查链路），**两种都要会用**。
> **命中就直接用坐标**（省掉截图）；**未命中才走截图找位置**，找到后补录。

> 💡 一句话：**定位由主 Agent 负责（截图+OCR+画框），子代理只负责"按给定坐标动手"。**

---

> ⚠️ **执行优先级声明**：涉及"操作手机 App / 查看 App 内容 / 点击界面"的任务，
> **优先使用本 Skill 的标准流程**，而非直接调用 `Automatic_ui_base` 或 `Automatic_ui_subagent` 裸操作。

## 📦 环境依赖：通知辅助组件（`com.operit.assist`）

本 Skill 的**通知能力依赖一个可选的辅助组件 App**（Operit辅助组件）：

| 状态 | 通知行为 |
|---|---|
| **已安装** `com.operit.assist` | 用 `am broadcast` 经它发通知 → **横幅弹出 + 自定义图标 + 震动** |
| **未安装** | 降级 `cmd notification post`（shell 通知）→ **静默，只进通知栏** |

- **发通知前必须先检查**：`pm list packages | grep com.operit.assist`
- **未安装时**：正常执行（降级），但**必须告知用户**去仓库 Release 安装以获得完整能力：
  `https://github.com/Leumc/Skills-Plugins/releases`（tag `Android-App`，文件 `Operit_Assist.apk`）
- 详细调用方式见 **步骤 5.5**。
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

> 📌 **数据库可以随时查，不是只在开头查一次。**
> 它是**持续可查的缓存**：每进入一个新界面、每开始一个子任务、每不确定某元素位置时——
> **都应该先 `query-screen` 或 `query-action` 查一下**，命中就直接用坐标，省掉截图。
> 查库成本极低（一条命令），比截图 + OCR + 画框快得多。
>
> **两种查询**：`query-action`（按操作查链路）/ `query-screen`（按界面查元素）——**都要会用**。

### 步骤 0：查询场景缓存（务必先做，**两种查询都要做**）

> 🚫 **最常见的漏做**：只查了「操作链路」（`query-action`），**没查「界面元素」（`query-screen`）**，
> 结果明明库里有坐标，还在那儿截图找位置。
> **规则：任何一次进入新界面 / 开始新任务，两种查询都要跑一遍。**

查询**场景数据库**（SQLite 三表结构）：

```bash
cd /sdcard/Download/Operit/skills/virtual_screen_auto/scripts

# 【查法1】按“操作”查 → 返回完整步骤链（知道要做什么时用）
python3 scene_db.py query-action --name "再来一单"

# 【查法2】按“界面”查 → 列出该界面所有已缓存元素+坐标（知道在哪个页面时用）
python3 scene_db.py query-screen --pkg com.sankuai.meituan --act "全部订单页"

# 【辅助】列出全部已缓存内容（不确定有什么、想摸底时用）
python3 scene_db.py list
```

#### 四种查询时机的对应做法

| 情形 | 该查什么 | 命令 |
|---|---|---|
| **知道要做的操作名**（如"再来一单"） | 查操作链路 | `query-action --name "<操作名>"` |
| **知道当前在哪个界面**（如"全部订单页"） | 查界面元素 | `query-screen --pkg <包名> --act "<界面名>"` |
| **两者都不确定** | 先摸底 | `list` → 看清有什么，再决定 |
| **进入一个新界面后**（每步操作之后） | **必查界面元素** | `query-screen --pkg <包名> --act "<当前界面>"` ← **最容易漏，务必做** |

> 💡 **关键认知**：数据库是**持续可查的缓存**，不是"只在开头查一次"。
> **每进入一个新界面，就应主动 `query-screen` 看这里有没有已缓存的元素**——
> 有 → 直接用坐标，跳过截图；没有 → 才走截图找位置流程。

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
- 🔁 **每次确认出新界面后，先 `query-screen` 查这个界面有没有已缓存元素**（再决定要不要截图找位置）：
  ```bash
  cd /sdcard/Download/Operit/skills/virtual_screen_auto/scripts
  python3 scene_db.py query-screen --pkg <包名> --act "<当前界面名>"
  ```
  - **有命中** → 直接用坐标，**跳过步骤 3 的截图流程**（这是数据库最大的价值）。
  - **无命中** → 才进入步骤 3 截图找位置，找到后补录。

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

### 步骤 4：让子代理点击（坐标必须已由主 Agent 定好）
**前提（硬性）**：手头已有**通过截图+OCR+画框校验得出的比例坐标**（或来自数据库命中）。
**没有坐标就不要进入这一步** —— 先回去做步骤 3。

- ✅ 正确：给子代理一个**写死的坐标**，只让它点。
  > "本任务只做一次点击：do(action=\"Tap\", element=[x,y])。点击后等待 N 秒，报告页面。不要重复点击，不要返回。"
- ❌ **禁止**："帮我点一下『再来一单』" / "找到『个人中心』并点击" / "点那个按钮"
  —— 这类让它自己找位置的说法，**一律不许**。
- 点击后**再次截图确认**结果（结果不对 → 回步骤 3 重新定位 + `fail` 记录）。

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

**【动作2：发系统通知】**

> **判断顺序（务必按此走）**：先看辅助 App 是否安装 → 装了用辅助 App（可横幅+图标+震动）；没装则降级为 shell 静默通知，**并在对话里明确告知用户去仓库 Release 安装**。

**① 先检查辅助 App 是否安装**（`super_admin:shell`）：
```bash
pm list packages | grep com.operit.assist
```
- **输出含 `package:com.operit.assist`** → 已安装，走 **②A**（推荐，体验最好）
- **无输出** → 未安装，走 **②B**（降级），并**必须告知用户去安装**（见下文）

**【②A · 已安装辅助 App】用广播发通知**（调用 `super_admin:shell`）：
```bash
am broadcast -a com.operit.notify.SHOW \
  -n com.operit.assist/com.operit.assist.notify.NotifyReceiver \
  --es title "Operit · 查询结果" \
  --es text "<结果>" \
  --ez vibrate true \
  --ez sound false \
  --ei id 1001
```
- 返回 **`Broadcast completed: result=-1, data="ok"`** = 成功（`result=-1` 即 `RESULT_OK`；失败时 `data` 为原因）。
- 效果：**横幅弹出 + 自定义图标 + 震动（无声音）**。
- ⚠️ 必须用**显式广播 `-n`**，不要用隐式 action。

**【②B · 未安装辅助 App】降级为 shell 静默通知**：
```bash
cmd notification post -t "Operit · 查询结果" -S bigtext "query" "<结果>"
```
- 效果：**纯文字、静默**，只进通知栏（无横幅/无自定义图标/无震动）。
- **纯文字，不加图标**（shell 通知的图标会被 ROM 强制替换为默认图标，加了也白加）。
- 返回含 `Notification(...)` 即成功。

> 📢 **未安装时必须在对话中告知用户**（原话参考）：
> 「本次用的是系统 shell 静默通知（只能在通知栏查看，无横幅/震动）。
> 想要**横幅弹出 + 自定义图标 + 震动**，请到仓库 Release 安装辅助组件：
> https://github.com/Leumc/Skills-Plugins/releases （tag `Android-App`，文件 `Operit_Assist.apk`）
> 安装后本 Skill 会自动切换到辅助组件发送通知。」

**实操示例**（查物流场景，两个动作都发）：

已安装辅助组件时：
```
# 1) Toast
debug_run_sandbox_script(source_code: "const r = await toolCall('toast', { message: '查询结果｜Switch Lite手柄壳(蓝)：派件中，预计今天送达·圆通' }); return { ok:true, r };", wait_ms: 8000)

# 2) 系统通知（辅助组件）
super_admin:shell(command: "am broadcast -a com.operit.notify.SHOW -n com.operit.assist/com.operit.assist.notify.NotifyReceiver --es title \"Operit · 查询结果\" --es text \"查询结果｜Switch Lite手柄壳(蓝)：派件中，预计今天送达·圆通\" --ez vibrate true --ez sound false --ei id 1001")
```

未安装辅助组件时：
```
# 2) 系统通知（降级为 shell 静默通知）
super_admin:shell(command: "cmd notification post -t \"Operit · 查询结果\" -S bigtext \"query\" \"查询结果｜Switch Lite手柄壳(蓝)：派件中，预计今天送达·圆通\"")
# 然后口头告知用户去 Release 安装
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
- 遇到 输密码/指纹/确认支付 等，**AI 停手**，发通知告知用户接管：
  - **已装辅助 App**（`pm list packages | grep com.operit.assist` 有输出）→ 用广播（可横幅，用户更容易及时看到）：
    ```bash
    am broadcast -a com.operit.notify.SHOW -n com.operit.assist/com.operit.assist.notify.NotifyReceiver --es title "Operit助手" --es text "美团订单待支付 ¥14.1，请在虚拟屏接管支付" --ez vibrate true --ez sound false
    ```
  - **未装辅助 App** → 降级 shell 通知，并告知用户去 Release 安装（同步骤 5.5）：
    ```bash
    cmd notification post -t "Operit助手" "task" "美团订单待支付 ¥14.1，请在虚拟屏接管支付"
    ```
- 用户在 **Operit 虚拟屏预览窗口**里直接操作（**不切主屏**，不中断会话）。

## 五、关键约束（踩过的坑）
1. **单次操作原则**：一次调用只做一个动作，由主Agent串接控场；不要给子代理下多步长任务（会乱跳/卡死/提前退出）。
2. **子代理坐标不可靠（核心）**：估的坐标可能偏很多（实测「再来一单」子代理估 [835,493]，实际 [886,255]，**偏差约 250px**）。
   **所以坐标必须由主 Agent"截图+OCR+画框"量出，绝不能交给子代理自己估。**
3. **禁止用 Note/Call_API 代替动作**：intent 里写明"必须真的执行 Swipe/Tap"。
4. **滑动惯性大**：滑一次→停下读屏→再决定；滑两次内容不变 = 到底。
5. **虚拟屏勿多开**：同一 App 只能在一个虚拟屏；用完 `close_all_virtual_displays`。
6. **截图黑屏**：页面跳转/弹窗瞬间可能截到黑屏（文件很小如 19KB），重新截图即可，不是防截屏。
7. **App 混淆**：普通微信用 `com.tencent.mm`，企业微信用 `com.tencent.wework`；用底部导航条区分。
8. **控件拿不到**：微信/企业微信屏蔽无障碍，`uiautomator dump` 为空；只能靠截图视觉识别。
9. **通知必须走辅助 App 优先**（见步骤 5.5）：先 `pm list packages | grep com.operit.assist` 判断，
   装了就用 `am broadcast -n com.operit.assist/com.operit.assist.notify.NotifyReceiver`（可横幅/图标/震动）；
   没装才降级 `cmd notification post`，**并且必须告知用户去 Release 安装**。
   ⚠️ **禁止**不检查就直接用 shell 通知——那样会白白丢掉横幅和震动。

### ⛔ 最容易犯的错（务必自检）

| 错误写法（✅禁止） | 正确写法 |
|---|---|
| 让子代理"找到『个人课表』并点击" | 主 Agent 截图→OCR 得 `[255,779]` → 子代理 `Tap [255,779]` |
| 让子代理"点右上角的『再来一单』" | 主 Agent 量出 `[886,255]` → 子代理 `Tap [886,255]` |
| 数据库 MISS 后直接让子代理去点 | 回步骤 3 截图定位 → 得坐标 → 再点 → 补录数据库 |
| 一次 intent 让子代理"做完整流程" | 一次只给一个动作，主 Agent 逐步串接 |
| 直接 `cmd notification post` 发通知 | **先查辅助 App**：装了→广播；没装→降级+告知用户装 |

> 🔁 **每次调用子代理前自检**：我给的坐标，**是量出来的吗**？不是 → 先去量。
>
> 🔁 **每次发通知前自检**：我查过 `com.operit.assist` 装没装吗？没查 → 先查。
>
> 🔁 **每次进入新界面自检**：我 `query-screen` 查过这个界面吗？没查 → 先查（命中就省掉截图）。

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
- **查询类操作 → 同时 ① 弹 Toast（`toolCall('toast',...)`）+ ② 发通知**（见步骤 5.5）。
  - 通知**优先走辅助 App**（`com.operit.assist` 广播，可横幅/图标/震动）；
  - **未装辅助 App 则降级为 shell 静默通知，并必须告知用户去 Release 安装辅助组件**：
    https://github.com/Leumc/Skills-Plugins/releases （tag `Android-App` / `Operit_Assist.apk`）。
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
