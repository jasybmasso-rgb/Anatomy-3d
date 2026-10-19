# Attribution — paroi abdominale Z-Anatomy

Fichier : `public/models/zanatomy-abdo.glb`.

Maillage de la paroi abdominale (droit de l’abdomen, oblique externe, oblique interne, transverse, gauche et droite) dérivé du modèle **Z-Anatomy**.

## Licences

- **Z-Anatomy** — Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).  
  https://creativecommons.org/licenses/by-sa/4.0/  
  Auteurs : Gauthier Kervyn (design, 3D, anatomie), Marcin Zielinski (script Blender).  
  Dépôt : https://github.com/Z-Anatomy/Models-of-human-anatomy  
  Fichier source : `Z-Anatomy/Startup.blend` dans `Z-Anatomy.zip`, daté du 2 mai 2023.

- **BodyParts3D** — les modèles Z-Anatomy en sont dérivés.  
  Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP).  
  « BodyParts3D, Copyright© The Database Center for Life Science licensed by CC Attribution-Share Alike 2.1 Japan. »  
  https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html

Toute redistribution de ce GLB doit rester sous **CC BY-SA 4.0** (compatible avec le share-alike de BodyParts3D). Le code de l’application (MIT) est distinct du maillage.

## Ce qui a été modifié

Extraction des quatre muscles (gauche et droite) depuis le blend Z-Anatomy, soudure des sommets, normales lissées, décimation **meshoptimizer** à **10 %** (`simplifyWithAttributes`, `LockBorder` + `PreserveFolds`, ~22,7 k triangles), puis compression **Draco** (edgebreaker, positions 14 bits, normales 10 bits). Pas de carte de normales.

La collection « Rectus sheath » de la source est vide : pas de gaine séparée. L’aponévrose des obliques et du transverse est dans le même maillage, même matière. L’application retire la nappe médiale opaque et conserve les aponévroses procédurales (opacité 50 %) pour la gaine des droits. La ligne blanche (338 triangles dans la source) n’était pas dans le jeu décimé ; un mince ruban procédural occupe l’interstice entre les deux droits.

Le muscle pyramidal de l’abdomen n’est pas dans ce fichier.

Le GLB est dans l’espace d’origine Z-Anatomy (Y-up, origine vers les pieds). L’application l’aligne sur le squelette au chargement (échelle 0,995, tangage +4°, translation sur la crête pubienne).
