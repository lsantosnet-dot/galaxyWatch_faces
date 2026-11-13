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
include(":watchface", ":wear", ":mobile")
