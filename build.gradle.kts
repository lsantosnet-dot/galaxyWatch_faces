import com.android.build.api.dsl.ApplicationExtension

plugins {
    id("com.android.application") version "8.13.2" apply false
}

/**
 * Configuração comum a TODOS os mostradores em faces/<nome>.
 *
 * Cada mostrador é um APK Watch Face Format (WFF): sem código, só XML + imagens.
 * O pacote é derivado do nome da pasta: faces/classic -> com.lsantos.watchfaces.classic.
 * O build.gradle.kts de cada mostrador só precisa aplicar o plugin e (opcionalmente)
 * subir o versionCode.
 */
subprojects {
    if (parent?.name != "faces") return@subprojects

    pluginManager.withPlugin("com.android.application") {
        extensions.configure<ApplicationExtension> {
            val id = "com.lsantos.watchfaces.${project.name.replace('-', '_')}"
            namespace = id
            compileSdk = 36
            defaultConfig {
                applicationId = id
                minSdk = 34          // Watch Face Format v2 exige Wear OS 5 (API 34)
                targetSdk = 36
                versionCode = 1
                versionName = "1.0"
            }
            // APK limpo: sem metadados de dependências nem META-INF extra
            dependenciesInfo { includeInApk = false; includeInBundle = false }
            packaging { resources { excludes += "/META-INF/**" } }
            buildTypes {
                getByName("release") {
                    isMinifyEnabled = false
                    vcsInfo.include = false
                    // Uso pessoal: assina com a chave debug para poder instalar via adb.
                    signingConfig = signingConfigs.getByName("debug")
                }
            }
        }

        // Watch face não tem código (hasCode=false): desliga a geração de classes.dex.
        tasks.configureEach {
            if (name.matches(Regex("(dexBuilder|mergeDex|mergeExtDex|mergeLibDex|mergeProjectDex)(Debug|Release)"))) {
                enabled = false
            }
        }
    }
}
