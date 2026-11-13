plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.lsantos.watchmarket"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.lsantos.watchmarket"   // igual ao do relógio
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/watchfaceAssets"))
}

// CLI oficial do Google que valida o watch face e gera o token exigido pela API Watch Face Push
val validatorCli: Configuration by configurations.creating
dependencies {
    implementation("com.google.android.gms:play-services-wearable:19.0.0")
    validatorCli("com.google.android.wearable.watchface.validator:validator-push-cli:1.1.0-alpha01") {
        isTransitive = false   // é um "fat jar": já traz tudo dentro
    }
}

// Compila o watch face e copia o APK para dentro do app do celular (assets/watchface.apk).
val copyWatchFace by tasks.registering(Copy::class) {
    dependsOn(":watchface:assembleRelease")
    from(project(":watchface").layout.buildDirectory.file("outputs/apk/release/watchface-release.apk"))
    into(layout.buildDirectory.dir("generated/watchfaceAssets"))
    rename { "watchface.apk" }
}

// Valida o APK e salva o token em assets/watchface.token (enviado junto com o APK ao relógio).
val generateToken by tasks.registering {
    dependsOn(copyWatchFace)
    val apk = layout.buildDirectory.file("generated/watchfaceAssets/watchface.apk")
    val tokenFile = layout.buildDirectory.file("generated/watchfaceAssets/watchface.token")
    inputs.file(apk)
    outputs.file(tokenFile)
    doLast {
        val proc = ProcessBuilder(
            "java", "-jar", validatorCli.singleFile.absolutePath,
            "-a", apk.get().asFile.absolutePath, "-p", "com.lsantos.watchmarket"
        ).redirectErrorStream(true).start()
        val text = proc.inputStream.bufferedReader().readText()
        proc.waitFor()
        val token = Regex("generated token: (\\S+)").find(text)?.groupValues?.get(1)
            ?: error("Validação do watch face falhou:\n$text")
        tokenFile.get().asFile.writeText(token)
    }
}
tasks.named("preBuild") { dependsOn(generateToken) }
