# Anatomy-3d

Application web d’**étude anatomique 3D** (MVP Phase 1) : un squelette BodyParts3D, des repères optionnels, une recherche de muscles, un zoom caméra et un panneau (nom, origine, insertion, mouvements).

Interface en **français canadien (fr-CA)**. Licence **MIT**.

## Démo Phase 1

- Au chargement : **squelette seulement**.
- Recherche avec **autocomplétion** (accents ignorés) sur le nom, le nom latin, les alias et l’identifiant.
- À la sélection : **muscle stylisé** + animation de caméra vers le foyer du muscle.
- **Réinitialiser** : muscle, panneau, champ de recherche et caméra.

Les chaînes myofasciales (Tom Myers), les nerfs et la superposition multi-éléments **ne font pas** partie de cette phase. Voir `docs/PLAN-PHASES.md` et `docs/SPEC-MVP.md`.

## Choix 3D : squelette BodyParts3D

Le squelette affiché est un **GLB fusionné** (`public/models/skeleton.glb`, **13,47 MiB**, normales incluses) dérivé de **BodyParts3D** (203 os, réduction 99 %). Voir `docs/ATTRIBUTION.md` pour le crédit **CC BY-SA 2.1 Japon** et les implications share-alike.

Repère scène : Y-up, stature ~1,7 m, origine près du bassin, face +Z. Les muscles restent des maillages **stylisés**. Les repères anatomiques (`src/data/landmarks.json`) sont des centroïdes / extrema de boîtes (v1 approximatif). Couches optionnelles (toggles **off** par défaut) : ligaments (`ligaments.glb`, tan — BP3D + bandes synthétiques aux articulations majeures) et fascias (`fascia.glb`, gris-bleu — tractus ilio-tibiaux BP3D + nappes synthétiques).

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

- Anatomy Trains / chaînes de Tom Myers
- Nerfs et plexus en 3D
- Sélection de plusieurs éléments à la fois
