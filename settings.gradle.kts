// Opcional: MAVEN_CENTRAL_MIRROR=<url> troca o Maven Central por um espelho
// (útil quando o Maven Central limita o IP). Sem a variável, usa o normal.
val centralMirror: String? = System.getenv("MAVEN_CENTRAL_MIRROR")

pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        if (centralMirror != null) maven(centralMirror) else mavenCentral()
    }
}
rootProject.name = "galaxywatch-faces"

// Cada pasta em faces/ que tenha um build.gradle.kts vira um módulo :faces:<nome>.
// Para criar um mostrador novo basta adicionar a pasta — não precisa editar este arquivo.
file("faces").listFiles()
    ?.filter { it.isDirectory && it.resolve("build.gradle.kts").exists() }
    ?.sortedBy { it.name }
    ?.forEach { include(":faces:${it.name}") }
