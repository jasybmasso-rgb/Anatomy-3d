# Attribution — maillages anatomiques

## BodyParts3D / Anatomography

Les maillages `public/models/skeleton.glb`, `public/models/ligaments.glb` et `public/models/fascia.glb` sont des **dérivés** (ou, pour les bandes synthétiques, des approximations pédagogiques alignées) des polygones **BodyParts3D** (arbre IS-A, réduction 99 %), filtrés respectivement aux **os**, à une **couche ligamentaire / fibreuse profonde** et aux **fascias / aponévroses**, fusionnés et renormalisés pour le web.

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

Modifications par rapport aux OBJ d’origine : sous-ensemble osseux, ligamentaire ou fascial ; conversion mètres ; Y-up ; stature ~1,7 m ; origine près du bassin ; orientation face +Z ; fusion en GLB. Les GLB ligaments et fascias sont alignés sur la même matrice `worldMatrix` que le squelette. Les bandes `source=synthetic` (ligaments articulaires majeurs, nappes fasciales absentes de BP3D) sont des approximations pédagogiques originales, pas des segmentations cadavériques.

### Reconstruction

```bash
python3 scripts/build_skeleton_glb.py
python3 scripts/build_ligaments_glb.py
python3 scripts/build_fascia_glb.py
# ou
bash scripts/build-skeleton-glb.sh
bash scripts/build-ligaments-glb.sh
bash scripts/build-fascia-glb.sh
```

Le script squelette télécharge `isa_BP3D_4.0_obj_99.zip`, `isa_element_parts.txt` (correspondance concept → fichier `FJ####`) et les listes IS-A depuis l’archive DBCLS, garde les **feuilles** descendantes de `FMA5018` (bone organ) plus le sternum, puis écrit `public/models/skeleton.glb` et `src/data/landmarks.json`.

Le script ligaments reprend les mêmes OBJ et applique `skeleton.meta.json` → `worldMatrix`. Inclusion BP3D : ligaments nommés + membranes interosseuses + rétinaculums des fléchisseurs. Les ligaments articulaires majeurs absents de BodyParts3D 4.0 (LCA/LCP, collatéraux, ilio-fémoral, gléno-huméraux, etc.) sont **synthétisés** comme bandes ancrées sur les repères (`source: synthetic`). Voir `src/data/ligaments.json`.

Le script fascias n’extrait de BP3D que les **tractus ilio-tibiaux** (FJ1423 / FJ1423M) : les parents « investing fascia / fascia lata » pointent vers les mêmes fichiers. Peau, graisse, TFL (muscle), septums nasaux et cérébraux exclus. Les rétinaculums du poignet restent dans `ligaments.glb`. Les nappes absentes (thoraco-lombaire, plantaire, palmaire, ligne blanche) sont synthétiques. Voir `src/data/fascia.json`.

Dépendances Python : `pip install -r scripts/requirements-skeleton.txt`.

Tailles commitées : squelette **13,47 MiB** (203 os) ; ligaments **1,66 MiB** (18 BP3D + 79 synthétiques) ; fascias **0,90 MiB** (2 BP3D + 8 synthétiques). Détail dans `public/models/*.meta.json`. Pas besoin de Git LFS.
