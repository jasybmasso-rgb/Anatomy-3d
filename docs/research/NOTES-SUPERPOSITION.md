# Notes — superposition multi-éléments (Phase 4)

**Statut :** recherche pour plus tard. Hors-scope du MVP.

## Pourquoi préparer l’état dès la Phase 1

La Phase 1 n’affiche **qu’un** muscle. Si la sélection était un booléen global unique (`window.MUSCLE = …`) ou un matériau unique réutilisé sans identifiant, passer à plusieurs calques forcerait une réécriture.

L’état Phase 1 reste volontairement **petit et remplaçable** :

```ts
type Phase1Selection = {
  selectedMuscleId: string | null;
};
```

Un seul champ `string | null` est suffisant aujourd’hui. Il ne doit pas être câblé comme « le » muscle du monde 3D sans passer par un sélecteur / store.

## Forme d’état visée en Phase 4

```ts
type LayerId = "muscles" | "chains" | "nerves";

type OverlaySelection = {
  muscleIds: string[];
  chainIds: string[];
  nerveIds: string[];
  activeLayers: LayerId[];
  opacityByLayer: Partial<Record<LayerId, number>>;
};

const emptySelection = (): OverlaySelection => ({
  muscleIds: [],
  chainIds: [],
  nerveIds: [],
  activeLayers: ["muscles"],
  opacityByLayer: { muscles: 1, chains: 0.85, nerves: 0.9 },
});
```

Migration depuis la Phase 1 :

```ts
function toOverlay(phase1: { selectedMuscleId: string | null }): OverlaySelection {
  const next = emptySelection();
  if (phase1.selectedMuscleId) next.muscleIds = [phase1.selectedMuscleId];
  return next;
}
```

## Règles UI envisagées

- Clic recherche Phase 1 ≡ remplacer `muscleIds` par un singleton (comportement actuel).
- Mode superposition : **ajouter / retirer** des ids sans vider les autres calques.
- Légende : une pastille par calque, opacité indépendante.
- Réinitialiser : revenir à `emptySelection()` + caméra d’ensemble (comme Phase 1).

## Rendu 3D

- Chaque calque = `group` séparé (muscles / chaînes / nerfs).
- Pas de couleur unique globale : table `id → matériau`.
- Depth / clipping : nerfs légèrement au-dessus des muscles si collision.

## Ce qu’il ne faut pas faire en Phase 1

- `let selected: Muscle` unique importé partout en mutable.
- Texture ou mesh unique « le muscle » sans `id`.
- URL ou store qui ne peut porter qu’une clé (`?muscle=` sans liste).

Une URL future du type `?muscles=a,b&chains=sbl` reste possible si l’état est déjà une liste.
