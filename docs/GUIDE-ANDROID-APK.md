# Guide d’installation — APK Android (debug)

APK de test **sideload**, signé avec la clé de debug Android (pas un store Play). Identifiant : `ca.anatomy3d.app`. Nom affiché : **Anatomy-3d**.

Cette version embarque le build Vite (WebView + WebGL) et les maillages GLB. Les commandes tactiles (orbite un doigt, pincement zoom, deux doigts panorama) sont les mêmes que sur le web.

## Télécharger l’APK

Lien public (GitHub Release, prerelease `apk-anatomy-pass-atlas`) — **enregistrer le fichier**, pas un artefact Cursor :

**https://github.com/jasybmasso-rgb/Anatomy-3d/releases/download/apk-anatomy-pass-atlas/Anatomy-3d-1.0-debug-anatomy-pass-atlas.apk**

Page de la release : https://github.com/jasybmasso-rgb/Anatomy-3d/releases/tag/apk-anatomy-pass-atlas

Fichier : `Anatomy-3d-1.0-debug-anatomy-pass-atlas.apk` (**~87 Mo**). Il n’est pas versionné dans Git ; le CDN GitHub envoie `Content-Disposition: attachment` pour forcer le téléchargement.

Cette build embarque les maillages à jour : fascias calés, ligaments sans têtes de champignon, nerfs synthetic-v3 (racines foraminales, sciatique sous le piriforme), paroi abdominale empilée, shader fibres rouges / tendons blancs, plus `nerves.glb`, `organs.glb` et `vessels.glb`.

```bash
npm install
npm run apk:debug
```

L’APK se trouve alors ici :

`android/app/build/outputs/apk/debug/app-debug.apk`

## Téléphone Android

1. Ouvrez le lien GitHub ci-dessus dans le navigateur (Chrome, Firefox). Le fichier doit se **télécharger** (pas s’installer tout de suite). S’il s’ouvre quand même : appuyez longuement → **Télécharger le lien** / **Enregistrer le fichier**.
2. Ouvrez le fichier depuis Téléchargements. Android affiche un avertissement **sources inconnues** / **installer des applications inconnues**.
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
- **Node.js 22+** est attendu par Capacitor 8 / `@capacitor/cli` (`engines.node >= 22`). Node 20 passe encore pour une partie des deps ; Node 18 ne fait qu’afficher `EBADENGINE`. Ne pas utiliser `npm audit fix --force` (cela rétrograderait Capacitor vers 6). L’avis `uuid` est dans `@capacitor/cli` → `xcode` (outillage de build), pas dans l’appli WebView.
