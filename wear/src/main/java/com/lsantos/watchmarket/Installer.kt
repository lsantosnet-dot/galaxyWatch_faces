package com.lsantos.watchmarket

import android.content.Context
import android.os.ParcelFileDescriptor
import androidx.wear.watchface.push.WatchFacePushManager
import java.io.File

/** Instala (ou atualiza) o watch face usando a API Watch Face Push do Wear OS 6. */
object Installer {

    /** Pacote do APK do watch face: <pacote deste app>.watchfacepush.<nome>. */
    const val FACE_PACKAGE = "com.lsantos.watchmarket.watchfacepush.classic"

    /** [token] é o token de validação gerado no build (ver mobile/build.gradle.kts). */
    suspend fun install(context: Context, apk: File, token: String): String {
        // 1) Adiciona (ou atualiza, se já existir) o watch face no "slot" do app.
        val manager = WatchFacePushManager(context)
        val existing = manager.listWatchFaces().installedWatchFaceDetails
            .firstOrNull { it.packageName == FACE_PACKAGE }

        val details = ParcelFileDescriptor.open(apk, ParcelFileDescriptor.MODE_READ_ONLY).use { fd ->
            if (existing != null) manager.updateWatchFace(existing.slotId, fd, token)
            else manager.addWatchFace(fd, token)
        }

        // 2) Tenta deixar o watch face ativo.
        return try {
            manager.setWatchFaceAsActive(details.slotId)
            "Watch face instalado e ativado!"
        } catch (e: Exception) {
            "Instalado, mas não foi possível ativar sozinho (${e.message}). " +
                "Segure o mostrador atual e escolha \"Classic Red\"."
        }
    }
}
