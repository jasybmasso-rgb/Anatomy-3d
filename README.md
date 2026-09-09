# Anatomy-3d

Application web d’**étude anatomique 3D** (MVP Phase 1) : un squelette humain simplifié, une recherche de muscles, un zoom caméra et un panneau (nom, origine, insertion, mouvements).

Interface en **français canadien (fr-CA)**. Licence **MIT**.

## Démo Phase 1

- Au chargement : **squelette seulement**.
- Recherche avec **autocomplétion** (accents ignorés) sur le nom, le nom latin, les alias et l’identifiant.
- À la sélection : **muscle stylisé** + animation de caméra vers le foyer du muscle.
- **Réinitialiser** : muscle, panneau, champ de recherche et caméra.

Les chaînes myofasciales (Tom Myers), les nerfs et la superposition multi-éléments **ne font pas** partie de cette phase. Voir `docs/PLAN-PHASES.md` et `docs/SPEC-MVP.md`.

## Choix 3D : squelette procédural

Le squelette est généré avec des **géométries Three.js** (capsules, sphères, plaques) plutôt qu’un fichier GLTF externe.

Raisons :

- pas de dépendance à un modèle sous licence tierce ;
- repère contrôlé (Y-up, stature ~1,7 m, origine près du bassin) aligné sur `focus` dans `src/data/muscles.json` ;
- les muscles sont des maillages **stylisés** (`meshHint`), pas des scans.

Un GLTF libre pourra remplacer le squelette plus tard sans changer le schéma de données, tant que le même repère est respecté.

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
| `src/data/README.md` | Schéma des données |
| `docs/SPEC-MVP.md` | Spécification Phase 1 |
| `docs/PLAN-PHASES.md` | Feuille de route |
| `docs/research/` | Notes Phase 2–4 (non implémentées) |

## Hors-scope actuel

- Anatomy Trains / chaînes de Tom Myers
- Nerfs et plexus en 3D
- Sélection de plusieurs éléments à la fois
