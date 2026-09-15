package com.operit.assist.notify

/**
 * 广播接口契约常量。
 *
 * Agent 侧调用示例：
 * ```
 * am broadcast -a com.operit.notify.SHOW \
 *   -n com.operit.assist/com.operit.assist.notify.NotifyReceiver \
 *   --es title "标题" --es text "正文" \
 *   --ez vibrate true --ez sound false --ei id 1001
 * ```
 */
object NotifyContract {

    /** 广播 Action。 */
    const val ACTION_SHOW = "com.operit.notify.SHOW"

    /** 通知渠道 ID。 */
    const val CHANNEL_ID = "operit_notify"

    /** Extras key。 */
    const val EXTRA_TITLE = "title"
    const val EXTRA_TEXT = "text"
    const val EXTRA_ID = "id"

    /** 是否震动，默认 true。 */
    const val EXTRA_VIBRATE = "vibrate"

    /** 是否响铃，默认 false。 */
    const val EXTRA_SOUND = "sound"

    /** 预留：自定义小图标资源名，默认使用 App 的 ic_stat_notify。 */
    const val EXTRA_ICON = "icon"

    /** 默认通知 ID。 */
    const val DEFAULT_ID = 1001

    /** 默认震动波形：等待 0ms，震 120ms，停 80ms，再震 120ms。 */
    val VIBRATION_PATTERN = longArrayOf(0, 120, 80, 120)
}
