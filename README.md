# Galaxy Watch Faces — "Classic Red"

Projeto de estudo: um app Android que, instalado no celular, envia e instala um
watch face (mostrador) no Galaxy Watch. O mostrador reproduz um relógio analógico
creme com números finos (12/3/6/9 em vermelho), ponteiro de segundos vermelho,
dia da semana, relógio digital com segundos, bateria e nascer/pôr do sol.

## Como funciona (3 peças)

```
 CELULAR (:mobile)                        RELÓGIO (:wear)                    :watchface
 ┌───────────────────┐  Data Layer       ┌──────────────────────┐   Watch   ┌───────────────┐
 │ botão "Instalar"  │  (canal Bluetooth)│ InstallerService     │   Face    │ APK sem código│
 │ contém o APK do   │ ───────────────►  │ recebe APK + token   │   Push    │ res/raw/      │
 │ watch face + token│   token + APK     │ WatchFacePushManager │ ────────► │  watchface.xml│
 └───────────────────┘ ◄───────────────  │  .addWatchFace(...)  │           │ + PNGs        │
        status                           └──────────────────────┘           └───────────────┘
```

| Módulo | O que é | Onde aprender |
|---|---|---|
| `watchface/` | O mostrador em si, no formato **Watch Face Format (WFF)**: um APK **sem código**, só XML + imagens. O relógio desenha tudo sozinho. | `watchface/src/main/res/raw/watchface.xml` (comentado) |
| `wear/` | App do relógio. Recebe o APK pelo Data Layer e instala com a API **Watch Face Push** (Wear OS 6+). | `wear/.../InstallerService.kt`, `Installer.kt` |
| `mobile/` | App do celular. Contém o APK do watch face dentro dos `assets` e o envia ao relógio. | `mobile/.../MainActivity.kt` |
| `tools/generate_images.py` | Gera **todas as imagens** (mostrador, ponteiros, ícones, preview) com Python + Pillow. | rode `python3 tools/generate_images.py` |

### Detalhes importantes
- **Regra de nome do pacote**: o watch face precisa se chamar
  `<pacote do app do relógio>.watchfacepush.<nome>` →
  `com.lsantos.watchmarket.watchfacepush.classic`.
- **Token de validação**: a API Watch Face Push exige que o APK passe pelo validador
  do Google. O build do `:mobile` roda o validador (`validator-push-cli`) e guarda o
  token em `assets/watchface.token`; o celular manda token + APK, e o relógio usa o token.
- O `watchface/build.gradle.kts` desliga a geração de `classes.dex` porque o validador
  rejeita qualquer código no APK do watch face.
- Os dois apps (`:mobile` e `:wear`) têm o **mesmo applicationId** — requisito do Data Layer.

## Compilar

Requisitos: JDK 17+, Android SDK (plataformas 35/36), Python 3 + Pillow (só se for regerar imagens).

```bash
echo "sdk.dir=/caminho/do/Android/Sdk" > local.properties
./gradlew :wear:assembleRelease :mobile:assembleRelease
```

Saídas:
- `mobile/build/outputs/apk/release/mobile-release.apk` (celular)
- `wear/build/outputs/apk/release/wear-release.apk` (relógio)

> Se o Maven Central devolver erro 429, use um espelho:
> `MAVEN_CENTRAL_MIRROR=https://maven-central.storage-download.googleapis.com/maven2/ ./gradlew ...`

## Instalar

1. **Celular**: instale `mobile-release.apk` (permita "fontes desconhecidas").
2. **Relógio** (sem Play Store, via adb sem fio):
   - Relógio: Configurações → Sobre o relógio → Informações do software → toque 5x em
     "Versão do software"; depois Opções do desenvolvedor → Depuração ADB e Depuração Wi-Fi.
   - PC: `adb pair IP:PORTA_PAREAMENTO` e `adb connect IP:PORTA`, então
     `adb install wear/build/outputs/apk/release/wear-release.apk`
3. Abra o app **Watch Faces** no relógio uma vez e conceda a permissão que ele pedir.
4. Abra o app no celular e toque em **Instalar no relógio**.

**Alternativa sem app (só para testar o desenho):**
`adb install watchface/build/outputs/apk/release/watchface-release.apk` e escolha
"Classic Red" na galeria de mostradores do relógio.

## Limitações / honestidade
- Foi **compilado e validado** com o validador oficial do Google, mas **não pôde ser
  testado em um relógio real** neste ambiente. O desenho (posições/tamanhos no XML) pode
  precisar de ajustes finos depois de ver no relógio.
- Watch Face Push exige **Wear OS 6 ou superior**. No Wear OS 6 cada app tem **1 slot** de
  watch face (instalar de novo atualiza o mesmo).
- Os APKs são assinados com a chave *debug* (projeto de estudo). Para publicar na Play
  Store é preciso uma chave própria.
