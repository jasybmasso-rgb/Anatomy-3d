# Anatomy-3d

Application web d’**étude anatomique 3D** (MVP Phase 1) : un squelette BodyParts3D, des repères optionnels, une recherche de muscles, un zoom caméra et un panneau (nom, origine, insertion, mouvements).

Interface en **français canadien (fr-CA)**. Licence **MIT**.

## Démo Phase 1

- Au chargement : **squelette seulement**.
- Recherche avec **autocomplétion** (accents ignorés) sur le nom, le nom latin, les alias et l’identifiant.
- À la sélection : **muscle stylisé** + animation de caméra vers le foyer du muscle.
- **Réinitialiser** : muscle, panneau, champ de recherche et caméra.

Les chaînes myofasciales (Tom Myers) sont une couche pédagogique. iOS / IPA hors de ce livrable.

## Choix 3D : squelette BodyParts3D

Le squelette affiché est un **GLB fusionné** (`public/models/skeleton.glb`, normales incluses) dérivé de **BodyParts3D** (os + cartilage hyalin / fibrocartilage disponible, réduction 99 %). Voir `docs/ATTRIBUTION.md` pour le crédit **CC BY-SA 2.1 Japon** et les implications share-alike.

Repère scène : Y-up, stature ~1,7 m, origine près du bassin, face +Z. Les muscles du MVP sont des maillages BodyParts3D (ou nappes synthétiques si le muscle est absent de BP3D 4.0), avec une texture de fibres fusiforme (ventre plus rouge, extrémités tendineuses plus claires). Les repères anatomiques (`src/data/landmarks.json`) sont des centroïdes / extrema de boîtes (v1 approximatif). Couches optionnelles (toggles **off** par défaut) : ligaments, fascias, **nerfs**, **organes** et **vaisseaux sanguins** (trois interrupteurs distincts — jamais organes+circulation fusionnés). Les nerfs périphériques majeurs absents de BodyParts3D 4.0 sont des tubes schématiques.

Reconstruction du GLB :

```bash
bash scripts/build-skeleton-glb.sh
```

## Prérequis

- Node.js 20+ recommandé
- npm

## Installation et lancement

```bash
npm install
npm run dev
```

Ouvrir l’URL affichée (par défaut `http://localhost:5173`).

## Production

```bash
npm run build
npm run preview
```

`npm run build` lance la vérification TypeScript puis le bundle Vite.

## APK Android (test sideload)

Application Capacitor (`ca.anatomy3d.app`). APK **debug** pour installation hors Play Store (squelette, muscles, ligaments, fascias, **nerfs, organes et vaisseaux** inclus) :

```bash
npm run apk:debug
```

Sortie : `android/app/build/outputs/apk/debug/app-debug.apk`. Guide d’installation (sources inconnues, Chromebook) : `docs/GUIDE-ANDROID-APK.md`.

## Structure utile

| Chemin | Rôle |
| --- | --- |
| `src/data/muscles.json` | 22 muscles du MVP |
| `src/data/landmarks.json` | Repères osseux (même espace que le GLB) |
| `public/models/skeleton.glb` | Squelette BodyParts3D (CC BY-SA 2.1 JP) |
| `docs/ATTRIBUTION.md` | Crédit et share-alike |
| `src/data/README.md` | Schéma des données |
| `docs/SPEC-MVP.md` | Spécification Phase 1 |
| `docs/PLAN-PHASES.md` | Feuille de route |
| `docs/research/` | Notes Phase 2–4 (non implémentées) |

## Hors-scope actuel

- IPA iOS
- Réécriture Anatomy Trains / Myers
- Fusion organes + vaisseaux dans une seule couche
