# Operit辅助组件 (assist_app)

> 本目录是 **Operit 专用辅助组件**：为 Operit Agent 提供原生 Android 能力补充，
> 使其能完成 shell 权限做不到的事情。当前首个模块为「通知投递」。

---

## 这个 App 解决什么问题

Operit 默认通过 shell（`uid 2000`）发通知，命令是：

```bash
cmd notification post -t "标题" -S bigtext "tag" "正文"
```

但该通知来源是 **`com.android.shell`**，被 vivo ROM 特殊对待，导致：

| 能力 | shell 通知 | 本 App 通知 |
|---|---|---|
| 弹 heads-up 横幅 | ❌ 只静默进通知栏 | ✅ |
| 自定义左侧小图标 | ❌ 被强制替换为默认图标 | ✅ |
| 震动 | ❌ 渠道禁用震动 | ✅ |
| 点击跳转 | ❌ Permission Denial | ✅ |

**根因**：只要是 `com.android.shell` 发的通知，vivo 就一视同仁地降级。

**解法**：用本 App 替代 shell 作为通知发送方——通知的「发送包名」变成 App 自己的包名，
ROM 的降级策略不再命中；且 App 可自建 `IMPORTANCE_HIGH` 渠道、自带图标、自带 `VibrationEffect`。

---

## 应用信息

| 项 | 值 |
|---|---|
| 应用名 | Operit辅助组件 |
| 包名 | `com.operit.assist` |
| 版本 | 1.0 (versionCode 1) |
| minSdk / targetSdk | 26 / 35 |
| 语言 / UI | Kotlin + Jetpack Compose (Material 3) |
| 构建 | Gradle Wrapper 9.1.0 + AGP 9.0.0 |
| 签名 | 自签名（Android Debug 证书） |

> ⚠️ 早期版本包名为 `com.operit.notifyassist`，现已更名为 `com.operit.assist`（视为新应用，旧版需卸载）。

---

## 通信链路

```
┌──────────────┐   am broadcast (显式, 带 extras)   ┌────────────────────┐
│ Operit Agent │ ─────────────────────────────────▶ │ NotifyReceiver     │
│ (shell,      │  -n <pkg>/.notify.NotifyReceiver   │        ↓           │
│  uid 2000)   │  --es title "..." --es text "..."  │ NotificationManager│
└──────────────┘                                    │ (自家包名 + HIGH)  │
                                                    └─────────┬──────────┘
                                                              ↓
                                                    横幅 / 自定义图标 / 震动
```

**关键设计**：使用 **显式广播（`-n 包名/接收器全名`）**，绕开 Android 8+ 对隐式广播的后台限制，
这是本方案可靠性的根本保证。

---

## 广播接口契约

### 通知投递

- **Action**：`com.operit.notify.SHOW`
- **组件**：`com.operit.assist/com.operit.assist.notify.NotifyReceiver`
- **接收器**：`android:exported="true"`，**故意不加 intent-filter**

| extra | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | String | 是 | 通知标题 |
| `text` | String | 是 | 通知正文 |
| `id` | int | 否 | 通知 ID（默认 `1001`；不同 id 可叠多条） |
| `vibrate` | boolean | 否 | 是否震动（默认 `true`） |
| `sound` | boolean | 否 | 是否响铃（默认 `false`） |
| `icon` | String | 否 | 预留：自定义小图标资源名 |

**调用示例**：

```bash
am broadcast \
  -a com.operit.notify.SHOW \
  -n com.operit.assist/com.operit.assist.notify.NotifyReceiver \
  --es title "Operit · 查询结果" \
  --es text "手柄壳：派件中，预计今天送达（圆通）" \
  --ez vibrate true \
  --ez sound false \
  --ei id 1001
```

**预期返回**：`Broadcast completed: result=-1, data="ok"`
（`result=-1` = `Activity.RESULT_OK`；失败时 `data` 为失败原因）

---

## 源码结构

```
assist_app/
├── app/src/main/
│   ├── AndroidManifest.xml
│   ├── java/com/operit/assist/
│   │   ├── MainActivity.kt                  # 主页：各模块状态与入口
│   │   ├── BootReceiver.kt                  # 开机重建渠道（保活）
│   │   ├── notify/                          # ★ 通知投递模块
│   │   │   ├── NotifyContract.kt            #   广播接口契约常量
│   │   │   ├── NotifyReceiver.kt            #   核心广播接收器
│   │   │   └── NotificationCompatBuilder.kt #   通知构建
│   │   └── ui/theme/                        #   主题（Color / Theme / Type）
│   └── res/                                 #   图标与字符串资源
├── gradle/libs.versions.toml                # 依赖版本目录
├── build.gradle.kts / settings.gradle.kts
├── setup_android_env.sh                     # ARM64 proot 环境初始化（替换 aapt2）
└── README.md
```

### 扩展方式

新增辅助功能时，在 `com.operit.assist` 下建独立子包（如 `clipboard/`、`file/`），
每个模块自带 Receiver 与契约，并在 `MainActivity` 的「功能模块」区添加状态卡片。

---

## 组件清单

| 组件 | 作用 |
|---|---|
| `MainActivity` | 主页：申请 `POST_NOTIFICATIONS`、发送测试通知、跳转系统通知设置 |
| `notify.NotifyReceiver` ★ | 核心：接收显式广播并发布 `IMPORTANCE_HIGH` 通知 |
| `BootReceiver` | 开机重建通知渠道（vivo 需用户手动加自启动白名单） |
| `notify.NotifyContract` | 广播接口契约常量 |
| `notify.NotificationCompatBuilder` | 统一构建通知（Receiver 与 Activity 共用） |

---

## 权限

- `android.permission.POST_NOTIFICATIONS`（Android 13+ 运行时申请）
- `android.permission.VIBRATE`
- `android.permission.RECEIVE_BOOT_COMPLETED`

最小权限原则，仅做「通知投递」这一件事。

---

## 构建

环境要求：**JDK 17+** + **Android SDK**。

```bash
# 1) 配置 SDK 路径（首次）
echo "sdk.dir=/opt/android-sdk" >> local.properties

# 2) （ARM64 proot 环境）初始化，替换 aapt2
chmod +x ./setup_android_env.sh && ./setup_android_env.sh

# 3) 构建
./gradlew assembleDebug
# 产物：app/build/outputs/apk/debug/app-debug.apk
```

> **注意**：构建产物（`app/build/`、`.gradle/`、`local.properties`、`*.apk`）不应提交到仓库。

---

## 安装与交付

APK 由**用户手动安装**（系统会提示「未知来源」，属正常）。

```bash
cp app/build/outputs/apk/debug/app-debug.apk \
   /sdcard/Download/Operit/assist_app/operit-assist.apk
```

---

## 图标

- **应用图标**：自适应图标（背景 / 前景 / 单色三层），覆盖 `mdpi~xxxhdpi` 5 种密度。
- **通知小图标**：`res/drawable/ic_stat_notify.xml`，白色剪影 + 透明背景
  （Android 系统只取 alpha 通道，彩色图会被渲染成白块）。

---

## 用户侧设置建议（vivo / iQOO）

1. 首次打开 App → 授予「通知」权限。
2. 系统设置 → 通知 → 本应用 → 允许「横幅通知」「锁屏通知」「震动」。
3. 电池 → 本应用 → 允许后台运行 / 允许自启动。
4. **不要「强行停止」本应用**（会导致静态接收器失效）。

---

## 实测验收（iQOO Z10 Turbo+ / vivo / Android 16）

| 验收项 | 结果 |
|---|---|
| 广播返回 `result=0` | ✅ `result=-1, data="ok"` |
| **横幅弹出**（关键） | ✅ `mRecentlyIntrusive=true`, `airtimeMs=5442` |
| 左侧小图标 = 自定义图标 | ✅ `icon=Icon(RESOURCE ... id=0x7f040007)` |
| 震动 ✓ / 声音 ✗ | ✅ 渠道 `enableVibration(true)`, `sound=null` |
| 渠道 IMPORTANCE_HIGH | ✅ `importance=4` |
| 多条通知叠放 | ✅ 不同 id 并存 |

---

## 技术备注

1. 必须使用 **显式广播 `-n`**，不要用 `intent-filter` + action 的隐式方式。
2. `am broadcast --help` 会报 `Unknown command`，**属正常**，命令本身可用。
3. 若横幅仍不弹，**先排查用户侧设置**（电池 / 自启动 / 横幅开关），再怀疑代码。
4. 本 App **不负责** UI 自动化，仅做「通知投递」。
