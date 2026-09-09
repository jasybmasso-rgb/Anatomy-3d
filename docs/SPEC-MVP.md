# Spécification MVP — Anatomy-3d (Phase 1)

Document de spécification du produit minimal viable. Langue de l’interface : **français canadien (fr-CA)**.

## Objectif

Permettre d’étudier un muscle à la fois sur un **squelette humain 3D**, via une recherche, un zoom caméra et un panneau d’information (nom, origine, insertion, mouvements).

Au chargement, **seul le squelette** est visible. Aucun muscle n’est sélectionné.

## Pile technique

- **Vite** + **React** + **TypeScript**
- **Three.js** via **@react-three/fiber** et **@react-three/drei**
- Données muscles : `src/data/muscles.json`
- Licence : **MIT**

## Comportements requis

### Squelette seul (défaut)

- À l’ouverture, la scène affiche un humain en os uniquement.
- Choix d’implémentation : **GLB BodyParts3D** (`public/models/skeleton.glb`, CC BY-SA 2.1 Japon). Voir `docs/ATTRIBUTION.md`.
- Repères osseux optionnels (`src/data/landmarks.json`), masqués par défaut.

### Recherche et autocomplétion

- Barre de recherche en tête d’application.
- Autocomplétion **insensible aux accents** et à la casse.
- Champs indexés : `name`, `nameLatin`, `aliases[]`, `id`.
- La sélection d’une suggestion affiche le muscle correspondant.

### Affichage du muscle + zoom

- Le muscle sélectionné apparaît comme un **maillage stylisé** (pas un scan réel), guidé par `meshHint` et ancré sur le squelette.
- La caméra s’anime vers `focus.position` à une distance `focus.distance`.
- Repère : **Y vers le haut**, figure d’environ **1,7 m**, origine de scène près du **bassin**, face +Z, pieds vers Y ≈ −0,9.

### Panneau latéral

Lorsque un muscle est sélectionné, le panneau affiche :

| Champ UI (fr-CA) | Source JSON |
| --- | --- |
| Nom | `name` |
| Nom latin | `nameLatin` |
| Origine | `origin` |
| Insertion | `insertion` |
| Mouvements | `actions[]` |

Sans sélection : état vide invitant à rechercher un muscle.

### Réinitialiser

Le bouton **Réinitialiser** :

1. retire le muscle affiché ;
2. vide le panneau (retour à l’état vide) ;
3. ramène la caméra à la vue d’ensemble du squelette ;
4. vide le champ de recherche.

## Modèle de sélection (évolutif)

Phase 1 utilise un seul identifiant :

```ts
selectedMuscleId: string | null
```

Ce n’est **pas** un verrou irréversible : l’état applicatif reste un objet de sélection remplaçable plus tard par des couches multiples (chaînes, nerfs, superposition). Voir `docs/research/NOTES-SUPERPOSITION.md`.

## Jeu de données Phase 1

Exactement **22 muscles** dans `src/data/muscles.json`, schéma :

- `id`, `name`, `nameLatin`, `aliases[]`
- `region` : `membre-supérieur` | `membre-inférieur` | `tronc` | `cou` | `épaule`
- `origin`, `insertion`, `actions[]`
- `focus` : `{ position: [x, y, z], distance }`
- `meshHint` : indice de forme pour le maillage stylisé

Contenu de niveau manuel d’anatomie (origines / insertions / actions), en français.

## Hors-scope (Phase 1)

**Ne pas implémenter** dans ce MVP :

- chaînes myofasciales de Tom Myers / Anatomy Trains ;
- nerfs, plexus, innervation 3D ;
- superposition multi-éléments (plusieurs muscles / couches à la fois) ;
- modèles photoréalistes, dissection, ou atlas commercial.

Ces sujets sont préparés uniquement sous forme de notes dans `docs/research/` et d’une architecture de sélection extensible.

## Critères d’acceptation

- `npm install` puis `npm run dev` lance l’application.
- `npm run build` réussit.
- Chargement = squelette seul.
- Recherche + autocomplétion fonctionnelles (accents ignorés).
- Sélection = muscle visible + zoom + panneau complet.
- Réinitialiser remet muscle, panneau et caméra à zéro.
