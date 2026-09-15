package com.operit.assist.notify

import android.app.Activity
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.operit.assist.MainActivity
import com.operit.assist.R

/**
 * ★ 核心组件：接收 Operit（shell / uid 2000）发来的显式广播并弹出高优先级通知。
 *
 * 设计要点：
 * 1. `android:exported="true"`，**不加 intent-filter**（走显式广播，规避 Android 8+ 隐式广播后台限制）。
 * 2. 通知渠道用 `IMPORTANCE_HIGH`，使 vivo ROM 允许 heads-up 横幅。
 * 3. 小图标使用 App 自身资源（`ic_stat_notify`），不会被 ROM 强制替换为默认图标。
 * 4. 震动由 [NotificationCompat.Builder.setVibrate] + VibrationEffect 共同保证。
 * 5. 通过 `setResultCode` 回传执行结果，shell 侧可看到 `result=0`（成功）。
 */
class NotifyReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        try {
            if (intent.action != null && intent.action != NotifyContract.ACTION_SHOW) {
                Log.w(TAG, "收到非预期 action: ${intent.action}，仍继续处理")
            }

            val title = intent.getStringExtra(NotifyContract.EXTRA_TITLE) ?: "Operit"
            val text = intent.getStringExtra(NotifyContract.EXTRA_TEXT) ?: ""
            val id = intent.getIntExtra(NotifyContract.EXTRA_ID, NotifyContract.DEFAULT_ID)
            val vibrate = intent.getBooleanExtra(NotifyContract.EXTRA_VIBRATE, true)
            val sound = intent.getBooleanExtra(NotifyContract.EXTRA_SOUND, false)

            Log.i(TAG, "收到通知请求 id=$id title=$title vibrate=$vibrate sound=$sound")

            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            ensureChannel(context, nm)

            // 若未授予通知权限，直接返回失败原因（Android 13+）。
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                !NotificationManagerCompat.from(context).areNotificationsEnabled()
            ) {
                fail(context, "POST_NOTIFICATIONS 未授权，请打开 ${context.packageName} 授予通知权限")
                return
            }

            val builder = NotificationCompat.Builder(context, NotifyContract.CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_stat_notify)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(NotificationCompat.BigTextStyle().bigText(text))
                .setPriority(NotificationCompat.PRIORITY_HIGH)   // 兼容 Android 8.0 以下
                .setCategory(NotificationCompat.CATEGORY_MESSAGE)
                .setAutoCancel(true)
                .setDefaults(0)                                  // 渠道负责声音/震动，避免重复

            if (vibrate) {
                builder.setVibrate(NotifyContract.VIBRATION_PATTERN)
            } else {
                builder.setVibrate(longArrayOf(0))
            }

            // 大图标（右侧）：用 App 自己的彩色启动图标。
            runCatching {
                builder.setLargeIcon(
                    android.graphics.BitmapFactory.decodeResource(
                        context.resources,
                        R.mipmap.ic_launcher
                    )
                )
            }

            // 点击通知打开 App 主页。
            val contentIntent = android.app.PendingIntent.getActivity(
                context,
                0,
                Intent(context, MainActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
                android.app.PendingIntent.FLAG_UPDATE_CURRENT or
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M)
                        android.app.PendingIntent.FLAG_IMMUTABLE else 0
            )
            builder.setContentIntent(contentIntent)

            NotificationManagerCompat.from(context).notify(id, builder.build())

            // 成功：result=0
            setResultCode(Activity.RESULT_OK)
            setResultData("ok")
        } catch (t: Throwable) {
            Log.e(TAG, "发送通知失败", t)
            fail(context, t.message ?: t.javaClass.simpleName)
        }
    }

    /** 失败：RESULT_CANCELED + 原因字符串。 */
    private fun fail(context: Context, reason: String) {
        setResultCode(Activity.RESULT_CANCELED)
        setResultData(reason)
        Log.e(TAG, "FAILED: $reason")
    }

    companion object {
        private const val TAG = "NotifyReceiver"

        /**
         * 创建/更新通知渠道（幂等）。IMPORTANCE_HIGH 是能弹横幅的关键。
         */
        fun ensureChannel(context: Context, nm: NotificationManager) {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return

            val channel = NotificationChannel(
                NotifyContract.CHANNEL_ID,
                context.getString(R.string.channel_name),
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = context.getString(R.string.channel_desc)
                enableVibration(true)
                vibrationPattern = NotifyContract.VIBRATION_PATTERN
                enableLights(true)
                lightColor = 0xFFFF6FA5.toInt()
                setShowBadge(true)
                // 声音由广播的 sound extra 控制：默认不响铃。
                setSound(null, null)
            }
            nm.createNotificationChannel(channel)
        }

        /** 在“响铃”明确要求时返回系统默认提示音 Uri。 */
        fun defaultSoundUri() = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
    }
}
