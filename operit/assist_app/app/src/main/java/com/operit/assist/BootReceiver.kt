package com.operit.assist

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.operit.assist.notify.NotifyReceiver

/**
 * 可选组件：开机后重建通知渠道，保证后续广播能正常弹通知。
 * 注意：vivo 等 ROM 需用户在系统设置中手动加入自启动白名单，本组件才会被触发。
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        try {
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            NotifyReceiver.ensureChannel(context, nm)
            Log.i("BootReceiver", "开机完成，通知渠道已就绪")
        } catch (t: Throwable) {
            Log.e("BootReceiver", "开机初始化失败", t)
        }
    }
}