package com.lsantos.watchmarket

import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.TextView

/** Tela simples no relógio: pede a permissão do Watch Face Push e mostra instruções. */
class MainActivity : Activity() {

    private val permission = "com.google.wear.permission.PUSH_WATCH_FACES"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val text = TextView(this).apply {
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            setPadding(48, 48, 48, 48)
        }
        setContentView(text)

        if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(permission), 1)
        }
        text.text = "Pronto para receber watch faces.\nAbra o app no celular e toque em \"Instalar\"."
    }
}
