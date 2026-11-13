package com.lsantos.watchmarket

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.CapabilityClient
import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import java.io.DataOutputStream
import kotlin.concurrent.thread

/**
 * Tela única do celular. Ao tocar em "Instalar", encontra o relógio com o app
 * "Watch Faces" instalado, abre um canal (Data Layer) e envia o APK do watch face.
 * O relógio valida, instala via Watch Face Push e responde o status.
 */
class MainActivity : Activity(), MessageClient.OnMessageReceivedListener {

    private lateinit var status: TextView
    private lateinit var button: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        status = TextView(this).apply {
            text = "Toque em Instalar para enviar o watch face \"Classic Red\" ao seu Galaxy Watch."
            textSize = 16f
        }
        button = Button(this).apply {
            text = "Instalar no relógio"
            setOnClickListener { sendWatchFace() }
        }
        setContentView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
            addView(status)
            addView(button)
        })
    }

    override fun onResume() {
        super.onResume()
        Wearable.getMessageClient(this).addListener(this)
    }

    override fun onPause() {
        Wearable.getMessageClient(this).removeListener(this)
        super.onPause()
    }

    /** Resposta do relógio com o resultado da instalação. */
    override fun onMessageReceived(event: MessageEvent) {
        if (event.path == "/watchface/status") show(String(event.data))
    }

    private fun show(msg: String) = runOnUiThread {
        status.text = msg
        button.isEnabled = true
    }

    private fun sendWatchFace() {
        button.isEnabled = false
        status.text = "Procurando o relógio…"
        thread(name = "send-watchface") {
            try {
                val nodes = Tasks.await(
                    Wearable.getCapabilityClient(this)
                        .getCapability("watchface_installer", CapabilityClient.FILTER_REACHABLE)
                ).nodes
                val node = nodes.firstOrNull()
                    ?: return@thread show(
                        "Relógio não encontrado. Instale o app \"Watch Faces\" (módulo wear) " +
                            "no Galaxy Watch e confirme que ele está conectado ao celular."
                    )

                runOnUiThread { status.text = "Enviando para ${node.displayName}…" }
                val channelClient = Wearable.getChannelClient(this)
                val channel = Tasks.await(channelClient.openChannel(node.id, "/watchface/apk"))
                // Protocolo: token (UTF) + bytes do APK
                val token = assets.open("watchface.token").bufferedReader().use { it.readText() }
                DataOutputStream(Tasks.await(channelClient.getOutputStream(channel))).use { out ->
                    out.writeUTF(token)
                    assets.open("watchface.apk").use { it.copyTo(out) }
                }
                channelClient.close(channel)
                runOnUiThread { status.text = "Enviado. Aguardando o relógio instalar…" }
            } catch (e: Exception) {
                show("Erro: ${e.javaClass.simpleName}: ${e.message}")
            }
        }
    }
}
