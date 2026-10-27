# Stabilité — Chromebook et Android WebView

Les plantages occasionnels venaient surtout de la **pression GPU / mémoire**, pas d’un seul bug JS.

## Causes identifiées

- **Sept GLB préchargés** au démarrage (`muscles` ~26 Mo, `skeleton` ~16 Mo, plus ligaments / viscères). Android WebView et Chromebook saturent vite.
- **Matériaux PBR** (`MeshPhysicalMaterial`, clearcoat, sheen) + ombres 1024 + `ContactShadows` + antialiasing + DPR 2.
- **Fuite fascia** : un nouveau matériau physique à chaque changement de sélection / chaîne, jamais libéré.
- **Perte de contexte WebGL** (mise en arrière-plan, OOM) : canvas mort sans message.
- **Tempête `pointermove`** sur WebView : OrbitControls + gestes deux doigts à 120 Hz.

## Mitigations

- Couches optionnelles (nerfs, organes, vaisseaux, ligaments, fascias) **montées seulement si allumées** — plus de `useGLTF.preload` de ces GLB.
- Profil bas de gamme (`CrOS`, Android WebView, ≤4 cœurs ou ≤4 Go) : DPR 1, pas d’AA, pas d’ombres de contact, cartes d’ombre 512, Phong/Standard à la place du Physical.
- Restauration WebGL : `webglcontextlost` / `webglcontextrestored` + remount du `Canvas`.
- Fascias : un matériau réutilisé, mis à jour en place.
- `pointermove` ignoré s’il arrive à moins de 8 ms (sauf pincement deux doigts).
- Muscles toujours **opaques** (`depthWrite`, pas de transparence) pour éviter les fuites de profondeur qui forcent le GPU.

La surbrillance de sélection est appliquée **dans le handler de pick** (registre Three.js), pas après le `useEffect` React ni après l’animation caméra.
