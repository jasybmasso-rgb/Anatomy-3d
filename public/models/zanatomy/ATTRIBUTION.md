# Z-Anatomy — couches du corps entier

Source : [Z-Anatomy / Models-of-human-anatomy](https://github.com/Z-Anatomy/Models-of-human-anatomy), fichier `Startup.blend` du **2 mai 2023**. Licence **CC BY-SA 4.0**. Dérivé de BodyParts3D, Copyright© 2008 The Database Center for Life Science, CC BY-SA 2.1 Japon.

Crédit :

> Z-Anatomy, CC BY-SA 4.0. Gauthier Kervyn (design, 3D, anatomie), Marcin Zielinski (script Blender). https://github.com/Z-Anatomy/Models-of-human-anatomy

Les sommets sont déjà dans l’espace de l’application (même calage que l’ancienne paroi abdominale : pivot `(0, 0.861, 0.052)`, cible `(0, -0.064, 0.094)`, échelle `0.995`, tangage `+4°` autour de X). Compression **Draco** (edgebreaker). Pas de meshopt.

| Fichier | Rôle | Octets | Triangles | Nœuds | Décimation |
| --- | --- | ---: | ---: | ---: | --- |
| `squelette.glb` | os et cartilages | 3 034 548 | 762 263 | 326 | aucune |
| `muscles.glb` | muscles (tendon calcanéen inclus) | 6 719 908 | 1 845 796 | 480 | aucune |
| `fascias.glb` | fascias, aponévroses, rétinaculums | 1 500 560 | 475 085 | 197 | aucune |
| `ligaments.glb` | ligaments | 1 204 604 | 300 497 | 370 | aucune |
| `organes.glb` | viscères | 2 671 928 | 955 567 | 300 | aucune |
| `organes-snc.glb` | encéphale, œil, méninges | 2 796 084 | 790 529 | 325 | meshoptimizer ~0,62 sur les gros maillages |
| `nerfs.glb` | nerfs, plexus, ganglions (pas l’encéphale) | 2 747 276 | 1 216 040 | 257 | aucune |
| `vaisseaux-extremites.glb` | vaisseaux de la main et du pied | 1 326 480 | 572 544 | 92 | aucune |
| `vaisseaux.glb` | autres vaisseaux | 5 066 652 | 1 587 888 | 566 | meshoptimizer ~0,50, erreur 0,003 |
| **Total** | | **27 068 040** | **8 506 209** | | |

Le squelette est toujours chargé en mode Z-Anatomy. Les autres fichiers ne se téléchargent que lorsque leur couche est cochée (les chaînes myofaciales chargent aussi muscles, fascias, ligaments et `organes.glb`). Sur profil bas (Chromebook, Android, ≤4 cœurs ou ≤4 Go), les tout petits maillages sont masqués tant que la caméra est loin et réapparaissent au zoom. Les matériaux sont `MeshStandard`, sans ombre sur ce profil.

Noms : français (fr-CA). Les muscles déjà dans `muscles.json` gardent cet identifiant et cette fiche. Le reste est une pièce cliquable (`src/data/zanatomyParts.json`), le nom anglais Z-Anatomy restant en latin d’affichage.

## Chaînes — pièces maintenant présentes

Aponévrose plantaire, aponévrose palmaire, rétinaculums des fléchisseurs et des extenseurs du poignet, septums intermusculaires médial et latéral du bras, fascia clavipectoral, aponévrose épicrânienne (aussi « fascia du cuir chevelu »), tendon calcanéen, ligament antérieur de la tête de la fibula, symphyse pubienne, langue. Le semi-épineux de la tête est le maillage que Z-Anatomy nomme *spinalis capitis*.

## Absents de Z-Anatomy (la station reste « pas encore modélisé »)

- Tendon rotulien / ligament patellaire (pas de maillage distinct ; la patella et les rétinaculums patellaires existent, pas le tendon)
- Fascia sternal
- Fascia endothoracique et péricarde comme nappe
- Septum intermusculaire postérieur de la cuisse (septs fémoraux médial et latéral seulement)
- Périoste du radius et de l’ulna
- Muscle pubo-rectal
- Nerf phrénique (collection vide)
- Rameau récurrent du nerf médian comme objet séparé
- Rameaux calcanéens médial et latéral nommés
- Nerf cutané sural latéral comme objet propre
- Nerfs digitaux dorsaux du sural comme objets propres
- Nerfs digitaux propres un par doigt (groupés par tronc et par côté)

Le fichier `zanatomy-abdo.glb` (paroi à 10 %) n’est plus affiché par le mode corps entier.
