# Guide d’installation — APK Android (debug)

APK de test **sideload**, signé avec la clé de debug Android (pas un store Play). Identifiant : `ca.anatomy3d.app`. Nom affiché : **Anatomy-3d**.

Cette version embarque le build Vite (WebView + WebGL) et les maillages GLB. Les commandes tactiles (orbite un doigt, pincement zoom, deux doigts panorama) sont les mêmes que sur le web.

## Télécharger l’APK

L’APK de cette exécution d’agent : artefact `Anatomy-3d-1.0-debug-viscera.apk` (**~60 Mo**, 59,7 Mio). Il n’est pas versionné dans Git.

Cette build embarque les trois couches viscérales : `nerves.glb` (nerfs), `organs.glb` (organes) et `vessels.glb` (vaisseaux sanguins), en plus du squelette, des muscles, ligaments et fascias.

```bash
npm install
npm run apk:debug
```

L’APK se trouve alors ici :

`android/app/build/outputs/apk/debug/app-debug.apk`

## Téléphone Android

1. Copiez l’APK sur l’appareil (USB, Drive, courriel, etc.).
2. Ouvrez le fichier. Android affiche un avertissement **sources inconnues** / **installer des applications inconnues**.
3. Autorisez l’installation pour l’app qui ouvre le fichier (Fichiers, Chrome, Drive…).
4. Installez, puis ouvrez **Anatomy-3d**.

Si l’installateur refuse : Paramètres → Sécurité (ou Applications) → **Installer des apps inconnues** → activez la source utilisée.

## Chromebook (applications Android)

1. Activez le Play Store / le conteneur Android si ce n’est pas déjà fait.
2. Dans ChromeOS : Paramètres → Applications → **Google Play Store** → Préférences Android → Sécurité → **Sources inconnues** (selon la version : « Installer des applis inconnues »).
3. Ouvrez l’APK depuis Fichiers et installez.

Le WebView du Chromebook doit prendre en charge WebGL. Si l’écran reste noir, mettez à jour Chrome / WebView système, ou testez d’abord sur un téléphone.

## Notes

- **Debug** : pas de signature de production. Désinstallez cette build avant d’installer une version Play Store du même identifiant.
- Premier lancement : les GLB (~56 Mo de maillages, dont ~6 Mo de nerfs/organes/vaisseaux) se chargent en mémoire ; attendez quelques secondes.
- WebGL 2 est préféré ; WebGL 1 reste un repli. OpenGL ES 2.0 est exigé.
- Pour reconstruire : `npm run apk:debug` (nécessite JDK 21 et le SDK Android API 36).
