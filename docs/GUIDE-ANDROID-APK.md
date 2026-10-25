# Guide d’installation — APK Android (debug)

APK de test **sideload**, signé avec la clé de debug Android (pas un store Play). Identifiant : `ca.anatomy3d.app`. Nom affiché : **Anatomy-3d**.

Cette version embarque le build Vite (WebView + WebGL) et les maillages GLB. Les commandes tactiles (orbite un doigt, pincement zoom, deux doigts panorama) sont les mêmes que sur le web.

## Télécharger l’APK

Lien public (GitHub Release, prerelease `apk-zanatomy-full`, 25 oct. 2026) — **enregistrer le fichier**, pas un artefact Cursor :

**https://github.com/jasybmasso-rgb/Anatomy-3d/releases/download/apk-zanatomy-full/Anatomy-3d-1.0-debug-zanatomy-full.apk**

Page de la release : https://github.com/jasybmasso-rgb/Anatomy-3d/releases/tag/apk-zanatomy-full

Fichier : `Anatomy-3d-1.0-debug-zanatomy-full.apk` (**90 944 757 octets**, ~87 Mo). SHA-256 : `41973b806be73572c84ab98a245d1636a3702985537ca329ee57dab1271c880d`. Il n’est pas versionné dans Git ; le CDN GitHub envoie `Content-Disposition: attachment` pour forcer le téléchargement.

Cette build (commit `006e0a0`, `versionCode` 2) remplace `apk-zanatomy-abdo` (11 oct.). Elle embarque le corps entier Z-Anatomy (un GLB Draco par système, chargé à l’ouverture de la couche), les modèles de chaînes (Myers, Mézière, GDS, Busquet), les correctifs des os de la main et du contexte WebGL, et l’icône fournie. Le visualiseur `zanatomy-full-original` n’est pas inclus.

**Désinstallez d’abord** l’APK d’octobre (`apk-zanatomy-abdo`) ou toute build plus ancienne du même identifiant. La clé debug de cette machine n’est pas celle qui a signé la release d’octobre (certificat SHA-256 `324c69c0…` contre `73d6d688…`). Android refuse la mise à jour tant que l’ancienne signature est installée.

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

- **Debug** : pas de signature de production. Désinstallez cette build avant d’installer une version Play Store du même identifiant. Désinstallez aussi `apk-zanatomy-abdo` avant celle-ci : les deux clés debug ne correspondent pas.
- Premier lancement : les GLB (corps entier Z-Anatomy plus les anciens maillages procéduraux) se chargent en mémoire à l’ouverture de chaque couche ; attendez quelques secondes.
- WebGL 2 est préféré ; WebGL 1 reste un repli. OpenGL ES 2.0 est exigé.
- Pour reconstruire : `npm run apk:debug` (nécessite JDK 21 et le SDK Android API 36).
- **Node.js 22+** est attendu par Capacitor 8 / `@capacitor/cli` (`engines.node >= 22`). Node 20 passe encore pour une partie des deps ; Node 18 ne fait qu’afficher `EBADENGINE`. Ne pas utiliser `npm audit fix --force` (cela rétrograderait Capacitor vers 6). L’avis `uuid` est dans `@capacitor/cli` → `xcode` (outillage de build), pas dans l’appli WebView.
