plugins { id("com.android.application") }

android {
    namespace = "com.lsantos.watchmarket.watchfacepush.classic"
    compileSdk = 36
    defaultConfig {
        // Regra do Watch Face Push: <pacote do app do relógio>.watchfacepush.<nome>
        applicationId = "com.lsantos.watchmarket.watchfacepush.classic"
        minSdk = 33
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }
    // Um watch face WFF não pode ter código nem metadados extras no APK
    // (o validador do Watch Face Push rejeita classes.dex e META-INF/*).
    dependenciesInfo { includeInApk = false; includeInBundle = false }
    packaging { resources { excludes += "/META-INF/**" } }
    buildTypes {
        release {
            isMinifyEnabled = false
            vcsInfo.include = false
            // Projeto de estudo: assina com a chave debug para o APK ser instalável.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

// O AGP gera um classes.dex só com as classes R. Como o watch face não tem código
// (hasCode=false), desligamos a geração de dex para o APK ficar só com XML + imagens.
tasks.configureEach {
    if (name.matches(Regex("(dexBuilder|mergeDex|mergeExtDex|mergeLibDex|mergeProjectDex)Release"))) {
        enabled = false
    }
}
