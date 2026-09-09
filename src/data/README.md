# Données anatomiques (`src/data`)

## `muscles.json`

Tableau de **22 muscles** (Phase 1). Chaque objet :

| Champ | Type | Rôle |
| --- | --- | --- |
| `id` | `string` | Clé stable (kebab-case français). Sert à la sélection. |
| `name` | `string` | Nom affiché (fr-CA). |
| `nameLatin` | `string` | Nom latin (nomenclature usuelle). |
| `aliases` | `string[]` | Synonymes, abréviations, formes sans accents — pour la recherche. |
| `region` | union | `membre-supérieur` \| `membre-inférieur` \| `tronc` \| `cou` \| `épaule` |
| `origin` | `string` | Origine osseuse / fasciale (manuel). |
| `insertion` | `string` | Insertion. |
| `actions` | `string[]` | Mouvements / actions principales. |
| `focus.position` | `[x,y,z]` | Point visé par la caméra (Y-up). Espace landmarks : bassin à Y=0, pieds ≈ -0,9, crâne ≈ 0,66. Un Y supérieur à 0,82 (pieds à 0) est recalé automatiquement. |
| `focus.distance` | `number` | Distance caméra–cible (mètres). |
| `meshHint` | `string` | Indice de forme pour le maillage stylisé (`src/scene/muscleMeshes.ts`). |

Import applicatif : `src/types/muscle.ts` + `src/data/loadMuscles.ts`.

La recherche normalise accents / casse sur `name`, `nameLatin`, `aliases` et `id` (`src/lib/search.ts`).

## Ce qui n’est pas ici (volontairement)

- Chaînes myofasciales → plus tard, fichier séparé (Phase 2).
- Nerfs → Phase 3.
- Listes de sélection multiple → Phase 4 (l’UI ne lit qu’un `id` à la fois).

Ne pas fusionner ces domaines dans `muscles.json` : garder des identifiants de muscles stables pour les relier ensuite.
