package com.operit.assist.notify

import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.operit.assist.R

/**
 * 统一构建通知的辅助类，[NotifyReceiver] 与 [MainActivity] 共用，避免重复代码。
 */
object NotificationCompatBuilder {

    fun build(
        context: Context,
        title: String,
        text: String,
        vibrate: Boolean = true,
        sound: Boolean = false
    ): android.app.Notification {
        val builder = NotificationCompat.Builder(context, NotifyContract.CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_notify)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .setDefaults(0)

        if (vibrate) builder.setVibrate(NotifyContract.VIBRATION_PATTERN)
        else builder.setVibrate(longArrayOf(0))

        if (sound) {
            builder.setSound(NotifyReceiver.defaultSoundUri())
        }

        runCatching {
            builder.setLargeIcon(
                android.graphics.BitmapFactory.decodeResource(context.resources, R.mipmap.ic_launcher)
            )
        }

        return builder.build()
    }

    fun areNotificationsEnabled(context: Context): Boolean =
        NotificationManagerCompat.from(context).areNotificationsEnabled()

    @Suppress("unused")
    fun sdkAtLeastO() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
}