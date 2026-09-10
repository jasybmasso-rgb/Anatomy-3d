# Attribution — maillages anatomiques

## BodyParts3D / Anatomography

Les maillages `public/models/skeleton.glb`, `public/models/ligaments.glb`, `public/models/fascia.glb` et `public/models/muscles.glb` sont des **dérivés** (ou, pour les pièces `synthetic-v2`, des approximations pédagogiques alignées) des polygones **BodyParts3D** (arbre IS-A, réduction 99 %), filtrés respectivement aux **os + cartilage**, à une **couche ligamentaire / fibreuse profonde**, aux **fascias** et aux **muscles squelettiques nommés**, fusionnés et renormalisés pour le web.

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

Modifications par rapport aux OBJ d’origine : sous-ensemble osseux et cartilagineux, ligamentaire, fascial ou musculaire ; conversion mètres ; Y-up ; stature ~1,7 m ; origine près du bassin ; orientation face +Z ; fusion en GLB ; décimation des muscles trop denses. Les GLB ligaments, fascias et muscles sont alignés sur la même matrice `worldMatrix` que le squelette. Le cartilage n’est **pas** une couche Couches : il est toujours affiché avec l’os (nœud `cartilage` dans `skeleton.glb`).

Pièces `source=synthetic-v2` (faisceaux ligamentaires majeurs en fascicules arrondis, nappes fasciales ouvertes) et `source=synthetic` (grand dorsal, droit de l’abdomen) : approximations pédagogiques originales, **pas** des segmentations cadavériques. Les capsules/bâtonnets v1, rubans rectangulaires et manchons cylindriques ne sont plus exportés.

### Reconstruction

```bash
python3 scripts/build_skeleton_glb.py
python3 scripts/build_ligaments_glb.py
python3 scripts/build_fascia_glb.py
python3 scripts/build_muscles_glb.py
# ou
bash scripts/build-skeleton-glb.sh
bash scripts/build-ligaments-glb.sh
bash scripts/build-fascia-glb.sh
bash scripts/build-muscles-glb.sh
```

Le script squelette télécharge `isa_BP3D_4.0_obj_99.zip`, `isa_element_parts.txt` (correspondance concept → fichier `FJ####`) et les listes IS-A depuis l’archive DBCLS, garde les **feuilles** descendantes de `FMA5018` (bone organ) plus le sternum, y ajoute le **cartilage** BodyParts3D disponible (cartilages costaux gauches/droits 1–7, disques intervertébraux nommés, cartilage thyroïde / cricoïde / aryténoïdes / corniculés / cunéiformes, épiglotte, cartilages nasaux septal / alaires / latéraux — fichiers FJ uniques), puis écrit `public/models/skeleton.glb` (nœuds `bones` + `cartilage`) et `src/data/landmarks.json` (os seulement). BodyParts3D 4.0 n’a pas de cartilage articulaire hyalin ni de ménisques.

Le script ligaments reprend les mêmes OBJ et applique `skeleton.meta.json` → `worldMatrix`. Inclusion BP3D : ligaments nommés + membranes interosseuses + rétinaculums des fléchisseurs. Les ligaments articulaires majeurs absents de BodyParts3D 4.0 (genou, hanche, épaule, coude, cheville) sont des **faisceaux de fascicules loftés à section ronde** (`source: synthetic-v2`), éventail aux insertions, plus minces au milieu. Pas de bâtonnets rachidiens. Voir `src/data/ligaments.json`.

Le script fascias n’extrait de BP3D que les **tractus ilio-tibiaux** (FJ1423 / FJ1423M). Nappes schématiques : fascia lata et fascia crural en **feuilles ouvertes** (pas de cylindres), plus une nappe thoraco-lombaire postérieure. Fascia antébrachial, aponévroses palmaire/plantaire et ligne blanche omis. Voir `src/data/fascia.json`.

Le script muscles importe **tous** les muscles squelettiques BodyParts3D 4.0 disponibles (organes / chefs / zones, hors face-langue-larynx-œil), chefs fusionnés sous un id sélectionnable. **Absent de BP3D 4.0** : grand dorsal et droit de l’abdomen. L’apparence des fibres (UV le long de l’axe origine→insertion + texture fusiforme ventre rouge / extrémités tendineuses claires) est calculée côté client. Textes O/I/actions : `src/data/muscles.json`. Catalogue maillages : `src/data/muscleMeshes.json`.

Dépendances Python : `pip install -r scripts/requirements-skeleton.txt`.

Détail des tailles dans `public/models/*.meta.json`. Pas besoin de Git LFS.
