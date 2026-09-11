# Notes — nerfs (Phase 3)

**Statut :** couche **Nerfs** livrée, distincte des organes et des vaisseaux.

Géométrie : maillages crâniens BodyParts3D 4.0 (fidélité conservée) + tubes schématiques plus fins (`synthetic-v2`) pour les grands troncs périphériques, calés sur le trajet usuel (cubital, sillon spiral, ligament inguinal, grande échancrure sciatique…). Ce n’est **pas** un atlas de dermatomes. Couleur atlas or-jaune, distincte de l’ivoire osseux et des viscères.

Les correspondances muscle ↔ nerf ci-dessous restent des pistes pédagogiques, non affichées comme overlay automatique.

## Intention

Esquisser un **schéma** et des **correspondances** grandes lignes (muscle ↔ tronc nerveux), pas un atlas complet des plexus.

## Schéma (esquisse)

```
                    [encéphale / moelle]
                            |
              +-------------+-------------+
              |                           |
        plexus cervical            plexus brachial
        (cou, SCM, trapèze*)         (C5–T1)
              |                           |
              |              +------+-----+------+------+
              |              |      |     |      |      |
              |           n. dorsal  n.   n.    n.     n.
              |           scapulaire supra rad. médian ulnaire
              |           / axillaire épineux
              |
        plexus lombaire              plexus sacral
        (L1–L4)                      (L4–S4)
              |                           |
         n. fémoral                  n. sciatique
         n. obturateur                    |
                                     tibial / fibulaire
```

\* Le trapèze est surtout n. accessoire (XI) + rameaux cervicaux : le schéma ci-dessus est volontairement simplifié.

## Idées de mapping (exemples Phase 1 → nerf principal)

Ces associations sont **pédagogiques** (innervation dominante souvent citée en manuel). Variantes et doubles innervations existent.

| `muscleId` | Piste de nerf principal |
| --- | --- |
| `biceps-brachial` | musculo-cutané |
| `triceps-brachial` | radial |
| `deltoide` | axillaire |
| `grand-pectoral` | pectoraux latéral et médial |
| `grand-dorsal` | thoraco-dorsal |
| `trapeze` | accessoire (XI) |
| `sterno-cleido-mastoidien` | accessoire (XI) + plexus cervical |
| `biceps-femoral` | sciatique (tibial / fibulaire selon le chef) |
| `semi-tendineux` | sciatique (portion tibiale) |
| `semi-membraneux` | sciatique (portion tibiale) |
| `droit-femoral` | fémoral |
| `vaste-lateral` | fémoral |
| `vaste-medial` | fémoral |
| `vaste-intermediaire` | fémoral |
| `grand-fessier` | glutéal inférieur |
| `iliopsoas` | plexus lombaire / fémoral |
| `gastrocnemien` | tibial |
| `soleaire` | tibial |
| `tibial-anterieur` | fibulaire profond |
| `droit-abdomen` | nerfs intercostaux inférieurs (thoraco-abdominaux) |
| `oblique-externe` | intercostaux, ilio-hypogastrique, ilio-inguinal |
| `supra-epineux` | supra-scapulaire |

## Données futures (ne pas créer en Phase 1)

Forme possible :

```json
{
  "id": "n-radial",
  "name": "Nerf radial",
  "nameLatin": "Nervus radialis",
  "roots": ["C5", "C6", "C7", "C8", "T1"],
  "muscleIds": ["triceps-brachial"]
}
```

Géométrie 3D : courbes le long des os (caténaires), pas des volumes musculaires.

## Hors-scope même en Phase 3 (sauf décision produit)

- Dermatome complet cliquable
- Neurodynamique clinique
- Lésions / syndromes canalaires comme diagnostic automatique
