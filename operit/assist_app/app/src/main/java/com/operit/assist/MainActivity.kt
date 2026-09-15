package com.operit.assist

import android.Manifest
import android.app.NotificationManager
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.NotificationManagerCompat
import com.operit.assist.notify.NotifyContract
import com.operit.assist.notify.NotifyReceiver
import com.operit.assist.notify.NotificationCompatBuilder
import com.operit.assist.ui.theme.NotifyAssistTheme

/**
 * 主页：展示各辅助功能模块的状态与入口。
 *
 * 当前包含：
 * - 通知投递（Notification Delivery）
 *
 * 后续新增辅助功能时，在下方「功能模块」区添加对应卡片即可。
 */
class MainActivity : ComponentActivity() {

    private val requestPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            Toast.makeText(
                this,
                if (granted) "通知权限已授予" else "未授予通知权限，通知将无法显示",
                Toast.LENGTH_LONG
            ).show()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // 提前建好通知渠道，让用户在系统设置里能看到它。
        NotifyReceiver.ensureChannel(
            this,
            getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        )

        setContent {
            NotifyAssistTheme {
                HomeScreen(
                    onRequestPermission = { requestPermission.launch(Manifest.permission.POST_NOTIFICATIONS) },
                    onSendTest = { sendTestNotification() },
                    onOpenSettings = { openNotificationSettings() }
                )
            }
        }

        // 首次启动自动引导一次授权。
        maybeAutoRequest()
    }

    private fun maybeAutoRequest() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    /** 发送一条本地测试通知，验证权限 + 横幅 + 震动。 */
    private fun sendTestNotification() {
        try {
            NotifyReceiver.ensureChannel(
                this,
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            )
            val nm = NotificationManagerCompat.from(this)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                !nm.areNotificationsEnabled()
            ) {
                Toast.makeText(this, getString(R.string.result_fail) + "未授予通知权限", Toast.LENGTH_LONG).show()
                return
            }
            nm.notify(
                NotifyContract.DEFAULT_ID,
                NotificationCompatBuilder.build(
                    this,
                    getString(R.string.test_title),
                    getString(R.string.test_text),
                    vibrate = true
                )
            )
            Toast.makeText(this, getString(R.string.result_ok), Toast.LENGTH_SHORT).show()
        } catch (t: Throwable) {
            Toast.makeText(this, getString(R.string.result_fail) + (t.message ?: ""), Toast.LENGTH_LONG).show()
        }
    }

    private fun openNotificationSettings() {
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
        } else {
            Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                .setData(android.net.Uri.parse("package:$packageName"))
        }
        runCatching { startActivity(intent) }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen(
    onRequestPermission: () -> Unit,
    onSendTest: () -> Unit,
    onOpenSettings: () -> Unit
) {
    val context = LocalContext.current
    var granted by mutableStateOf(context.hasNotificationPermission())

    Scaffold(
        topBar = {
            TopAppBar(title = {
                Column {
                    Text(stringRes(R.string.app_name), fontWeight = FontWeight.Bold)
                    Text(
                        stringRes(R.string.subtitle),
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            })
        }
    ) { inner ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // ── 状态卡片 ──
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = if (granted) Color(0xFFE8F5E9) else Color(0xFFFFEBEE)
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(stringRes(R.string.status_title), fontWeight = FontWeight.Bold, fontSize = 15.sp)
                    Text(
                        if (granted) stringRes(R.string.status_ok) else stringRes(R.string.status_no_perm),
                        color = if (granted) Color(0xFF2E7D32) else Color(0xFFC62828),
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(stringRes(R.string.status_channel_ok), fontSize = 12.sp, color = Color(0xFF555555))
                }
            }

            if (!granted) {
                Button(onClick = { onRequestPermission(); granted = context.hasNotificationPermission() },
                    modifier = Modifier.fillMaxWidth()) {
                    Text(stringRes(R.string.grant_button))
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = { onSendTest(); granted = context.hasNotificationPermission() },
                    modifier = Modifier.weight(1f)
                ) { Text(stringRes(R.string.test_button)) }
                OutlinedButton(onClick = onOpenSettings, modifier = Modifier.weight(1f)) {
                    Text(stringRes(R.string.open_settings_button), fontSize = 12.sp)
                }
            }

            // ── 使用说明 ──
            Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(stringRes(R.string.guide_title), fontWeight = FontWeight.Bold, fontSize = 15.sp)
                    HorizontalDivider()
                    Text(stringRes(R.string.guide_body), fontSize = 13.sp, lineHeight = 21.sp)
                }
            }

            // ── 调用命令 ──
            Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(stringRes(R.string.cmd_title), fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        OutlinedButton(onClick = {
                            val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                            cm.setPrimaryClip(ClipData.newPlainText("cmd", context.getString(R.string.cmd_body)))
                            Toast.makeText(context, context.getString(R.string.copied), Toast.LENGTH_SHORT).show()
                        }) { Text(stringRes(R.string.copy_button), fontSize = 12.sp) }
                    }
                    HorizontalDivider()
                    Text(
                        stringRes(R.string.cmd_body),
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 17.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun stringRes(id: Int): String = LocalContext.current.getString(id)

private fun Context.hasNotificationPermission(): Boolean =
    NotificationManagerCompat.from(this).areNotificationsEnabled()