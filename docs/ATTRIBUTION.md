# Attribution — maillages anatomiques

## BodyParts3D / Anatomography

Le squelette 3D (`public/models/skeleton.glb`) est un **dérivé** des maillages polygonaux **BodyParts3D** (arbre IS-A, réduction 99 %), filtrés aux **os** uniquement, fusionnés et renormalisés pour le web.

**Crédit exigé (libellé officiel) :**

> BodyParts3D, Copyright© 2008 The Database Center for Life Science licensed by CC Attribution-Share Alike 2.1 Japan

- Licence : [Creative Commons Attribution-Share Alike 2.1 Japan](https://creativecommons.org/licenses/by-sa/2.1/jp/deed.en)
- Producteur : [Database Center for Life Science (DBCLS)](https://dbcls.rois.ac.jp/), Research Organization of Information and Systems
- Site d’origine : http://lifesciencedb.jp/bp3d/
- Archive de téléchargement : https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Publication : Mitsuhashi N. et al., *BodyParts3D: 3D structure database for anatomical concepts*, Nucleic Acids Research, 2009.
- DOI de la base : [10.18908/lsdba.nbdc00837-000](https://doi.org/10.18908/lsdba.nbdc00837-000)

### Share-alike (obligatoire pour le maillage)

Toute **redistribution du GLB** ou d’un autre dérivé des maillages BodyParts3D doit rester sous **CC BY-SA 2.1 Japon** (ou une licence compatible). Cela **ne s’applique pas** automatiquement au code applicatif (MIT) : le code et le jeu de données musculaires textuels sont distincts du dérivé 3D.

Modifications par rapport aux OBJ d’origine : sous-ensemble osseux seulement ; conversion mètres ; Y-up ; stature ~1,7 m ; origine près du bassin ; orientation face +Z ; fusion en un seul GLB.

### Reconstruction

```bash
python3 scripts/build_skeleton_glb.py
# ou
bash scripts/build-skeleton-glb.sh
```

Le script télécharge `isa_BP3D_4.0_obj_99.zip`, `isa_element_parts.txt` (correspondance concept → fichier `FJ####`) et les listes IS-A depuis l’archive DBCLS, garde les **feuilles** descendantes de `FMA5018` (bone organ) plus le sternum (manubrium, corps, xiphoïde), puis écrit `public/models/skeleton.glb` et `src/data/landmarks.json`.

Dépendances Python : `pip install -r scripts/requirements-skeleton.txt`.

Taille actuelle du dérivé commité : **10,21 MiB** (`public/models/skeleton.glb`, 203 os, ~284 k sommets, réduction source 99 %). Détail dans `public/models/skeleton.meta.json`. Pas besoin de Git LFS sous la limite GitHub (100 Mo).
