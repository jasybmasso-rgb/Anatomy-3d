# Notes — nerfs

**Statut :** couche **Nerfs** distincte des organes et des vaisseaux.

## Géométrie (honnête)

| Source | Contenu |
| --- | --- |
| **BodyParts3D 4.0** | Nerfs crâniens / orbitaires (optique, trochléaire, oculomoteur, ophtalmique, ciliaires…). Fidélité cadavérique conservée. |
| **synthetic-v3** | Grands troncs périphériques **absents de BP3D** : plexus brachial (racines C5–T1), médian, ulnaire, radial, axillaire, musculo-cutané, plexus lombaire (L2–L4), fémoral, obturateur, **sciatique (L4–S3, sous le piriforme)**, tibial, fibulaire, glutéal inférieur, phrénique (C3–C4). |

Les tubes `synthetic-v3` sont des **schémas pédagogiques** loftés sur des repères osseux, avec sorties foraminales visibles. Ce ne sont **pas** des segmentations IRM/cadavre. Le sciatique est calé sous le bord inférieur du muscle piriforme (BP3D) pour illustrer un conflit de type « sciatique sous piriforme ».

Couleur atlas **or-jaune** (`#f6d648`), distincte du rouge musculaire, de l’ivoire osseux et des vaisseaux. Troncs plus fins que v1/v2.

Reconstruction sans re-télécharger BP3D : `python3 scripts/rebuild_synthetic_nerves.py`.

## Intention clinique

Lorsque la couche Nerfs est allumée et que seuls quelques muscles sont visibles, on peut étudier un **trajet d’enclavement** (ex. sciatique profond au piriforme). Les racines sortent du rachis (foramens) avant de former les plexus.

Les correspondances muscle ↔ nerf ci-dessous restent des pistes pédagogiques, non affichées comme overlay automatique.

## Schéma

```
                    [encéphale / moelle]
                            |
              +-------------+-------------+
              |                           |
        plexus cervical            plexus brachial
        (phrénique C3–C4)            (C5–T1)
                                          |
                             médian / ulnaire / radial / axillaire
              |
        plexus lombaire              plexus sacral
        (L2–L4)                      (L4–S3)
              |                           |
         n. fémoral                  n. sciatique
         n. obturateur               (sous le piriforme)
                                          |
                                     tibial / fibulaire
```

## Hors-scope

- Dermatome complet cliquable
- Neurodynamique clinique automatique
- Variantes (sciatique trans-piriforme, etc.)
