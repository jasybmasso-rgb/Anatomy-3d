# Feuille de route — Anatomy-3d

Les phases sont **séquentielles**. Les phases 2 et suivantes ne commencent **pas** tant que la Phase 1 n’est pas **acceptée**.

## Phase 1 — Application de base (MVP)

**Statut cible :** DONE lorsque l’application décrite dans `docs/SPEC-MVP.md` fonctionne.

Périmètre :

- squelette 3D BodyParts3D (GLB) seul au chargement, repères optionnels ;
- recherche + autocomplétion de 22 muscles ;
- affichage stylisé d’un muscle, zoom caméra, panneau (nom, origine, insertion, mouvements) ;
- réinitialisation ;
- pile Vite + React + TypeScript + R3F + drei ;
- licence MIT.

Livrable : application utilisable, `npm run build` vert, documentation de spec et de données.

**Règle :** aucune fonctionnalité de chaîne, de nerf ou de multi-sélection dans cette phase.

## Phase 2 — Chaînes myofasciales (Tom Myers)

**Démarre seulement après acceptation de la Phase 1.**

Périmètre envisagé :

- visualisation pédagogique des lignes type Anatomy Trains (SBL, SFL, LL, SPL, DFL, lignes du bras, lignes fonctionnelles) ;
- bascule « muscle isolé » vs « chaîne » ;
- données séparées (ne pas surcharger `muscles.json` au-delà d’identifiants de lien).

Notes préparatoires : `docs/research/NOTES-ANATOMY-TRAINS.md`.

Ce n’est **pas** une copie d’ouvrage : modèle pédagogique, sources citées, textes originaux.

## Phase 3 — Nerfs, organes, circulation

**Statut :** couches Couches distinctes livrées (nerfs / organes / vaisseaux sanguins). Pas un atlas neurologique clinique.

Périmètre :

- trois interrupteurs **Nerfs**, **Organes**, **Vaisseaux sanguins** (jamais fusionnés) ;
- maillages BodyParts3D + troncs nerveux schématiques si absents de BP3D 4.0 ;
- recherche et fiche pour les structures nommées.

Notes préparatoires historiques : `docs/research/NOTES-NERFS.md`.

## Phase 4 — Superposition multi-éléments

**En dernier.**

Périmètre envisagé :

- plusieurs identifiants actifs à la fois (muscles, chaînes, nerfs) ;
- calques, opacité, légende ;
- état de sélection multi-couches (voir `docs/research/NOTES-SUPERPOSITION.md`).

La Phase 1 a volontairement un `selectedMuscleId: string | null` **remplaçable**, sans hack global unique irrémédiable.

## Résumé

| Phase | Contenu | Dépend de |
| --- | --- | --- |
| 1 | Base : squelette, 1 muscle, recherche, panneau | — |
| 2 | Chaînes myofasciales Tom Myers | Phase 1 acceptée |
| 3 | Nerfs | Phase 1 acceptée ; typiquement après 2 |
| 4 | Superposition multi-éléments | Phases précédentes stables |
