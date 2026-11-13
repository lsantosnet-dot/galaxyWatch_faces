package com.lsantos.watchmarket

import android.util.Log
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.ChannelClient
import com.google.android.gms.wearable.Wearable
import com.google.android.gms.wearable.WearableListenerService
import kotlinx.coroutines.runBlocking
import java.io.DataInputStream
import java.io.File
import kotlin.concurrent.thread

/**
 * Serviço acordado pelo Google Play Services quando o celular abre um canal
 * "/watchface/apk". Recebe o arquivo, instala o watch face e responde o status.
 */
class InstallerService : WearableListenerService() {

    override fun onChannelOpened(channel: ChannelClient.Channel) {
        if (channel.path != "/watchface/apk") return
        val channelClient = Wearable.getChannelClient(this)
        val appContext = applicationContext

        thread(name = "watchface-install") {
            val message = try {
                // Protocolo: primeiro o token (UTF), depois os bytes do APK até o fim.
                val input = DataInputStream(Tasks.await(channelClient.getInputStream(channel)))
                val apk = File(appContext.cacheDir, "watchface.apk")
                input.use {
                    val token = it.readUTF()
                    apk.outputStream().use { out -> it.copyTo(out) }
                    runBlocking { Installer.install(appContext, apk, token) }
                }
            } catch (e: Exception) {
                Log.e("WatchFaceInstall", "Falha", e)
                "Erro: ${e.javaClass.simpleName}: ${e.message}"
            }
            Log.i("WatchFaceInstall", message)
            runCatching {
                Tasks.await(
                    Wearable.getMessageClient(appContext)
                        .sendMessage(channel.nodeId, "/watchface/status", message.toByteArray())
                )
            }
        }
    }
}
