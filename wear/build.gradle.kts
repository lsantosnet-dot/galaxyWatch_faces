plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.lsantos.watchmarket"
    compileSdk = 36
    defaultConfig {
        // MESMO applicationId do app do celular (necessário para o Data Layer
        // entregar mensagens/arquivos entre os dois) e prefixo do pacote do watch face.
        applicationId = "com.lsantos.watchmarket"
        minSdk = 36           // Watch Face Push exige Wear OS 6 (API 36)
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
}

dependencies {
    implementation("androidx.wear.watchface:watchface-push:1.3.0-alpha07")
    implementation("com.google.android.gms:play-services-wearable:19.0.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
}
