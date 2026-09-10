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
| `focus.distance` | `number` | Distance caméra–cible (mètres). Recalculée depuis le maillage (moitié droite, patient). |
| `meshHint` | `string` | Indice de forme de repli si le GLB n’expose pas le nœud. |
| `meshSource` | `bodyparts3d` \| `synthetic` | Provenance du maillage 3D. |

Maillages : `public/models/muscles.glb` (nœud = `id`) + catalogue `src/data/muscleMeshes.json`. **20** muscles BP3D ; **grand dorsal** et **droit de l’abdomen** synthétiques (absents de BP3D 4.0). L’UI peut afficher le muscle sélectionné ou tout le jeu (`Afficher tous les muscles`), avec masquage fin.

Import applicatif : `src/types/muscle.ts` + `src/data/loadMuscles.ts`.

## `landmarks.json`

Repères osseux nommés, **même espace** que `public/models/skeleton.glb` (Y-up, mètres, origine bassin, face +Z). Généré par `scripts/build_skeleton_glb.py` à partir des centroïdes / extrema (ou bandes de percentiles) des maillages BodyParts3D.

| Champ | Rôle |
| --- | --- |
| `id` | Clé stable (kebab-case). Prévue pour lier plus tard origines / insertions. |
| `name` | Nom affiché (fr-CA). |
| `nameLatin` | Nom latin / TA usuel. |
| `region` | Région anatomique. |
| `position` | `[x, y, z]` dans l’espace du GLB. |
| `source` | Identifiant FMA, nom de pièce, mode de placement. |

**Précision v1** : points approximatifs (centroïde ou extrémité de boîte), à raffiner manuellement avant un binding origine/insertion. Le toggle UI « Afficher les repères » est **désactivé** par défaut.

## `ligaments.json`

Catalogue des pièces du `ligaments.glb` (même espace que le squelette). Toggle « Afficher les ligaments » **off** par défaut.

| Champ | Rôle |
| --- | --- |
| `id` | Clé stable. |
| `name` / `nameLatin` | Noms FR et latin. |
| `region` / `joint` | Localisation. |
| `source` | `bodyparts3d` ou `synthetic-v2`. |
| `notes` | Inclusion / précision. Les synthétiques sont des approximations pédagogiques. |
| `fmaId` / `fileIds` | Identifiants BodyParts3D (vides si synthétique). |

BodyParts3D 4.0 n’expose pas les ligaments majeurs des articulations (LCA, ilio-fémoral, etc.). Ceux-ci sont **synthétisés** comme faisceaux de fascicules arrondis ancrés sur `landmarks.json`.

## `fascia.json`

Catalogue du `fascia.glb`. Toggle « Afficher les fascias » **off** par défaut. Matériau gris-bleu translucide (distinct du tan ligamentaire et de l’ivoire osseux).

| Champ | Rôle |
| --- | --- |
| `id` | Clé stable. |
| `name` / `nameLatin` | Noms FR et latin. |
| `region` | Localisation. |
| `source` | `bodyparts3d` ou `synthetic-v2`. |
| `notes` | Inclusion / approximation. |
| `fmaId` / `fileIds` | Identifiants BodyParts3D (vides si synthétique). |

BP3D 4.0 n’a quasiment pas de nappes fasciales distinctes : les parents « investing fascia » et « fascia lata » se réduisent aux **tractus ilio-tibiaux** (FJ1423 / FJ1423M). Peau, graisse, TFL et septums nasaux / cérébraux exclus. Les rétinaculums du poignet restent dans `ligaments.json`. Fascia lata / crural : feuilles ouvertes schématiques. Fascia thoraco-lombaire : nappe postérieure. Fascia antébrachial et aponévroses palmaire / plantaire omis. Lacunes documentées dans `gaps`.

La recherche normalise accents / casse sur `name`, `nameLatin`, `aliases` et `id` (`src/lib/search.ts`).

## `chains.json`

Lignes pédagogiques type Anatomy Trains (Tom Myers) : `id`, `sigle`, noms FR+EN, courte description originale, `tint`, `muscleIds[]` mappés au catalogue. Disclaimer dans le fichier. L’UI (Couches → Chaînes myofaciales) permet la multi-sélection.

## Ce qui n’est pas ici (volontairement)

- Nerfs → Phase 3.
- Atlas vasculaire / organes.

Ne pas fusionner ces domaines dans `muscles.json` : garder des identifiants de muscles stables pour les relier.
