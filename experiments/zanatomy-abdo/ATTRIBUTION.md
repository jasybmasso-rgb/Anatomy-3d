# Attribution — essai Z-Anatomy, paroi abdominale

Ce dossier est une expérience isolée. Il ne modifie pas l’application.

Les maillages dérivent du modèle **Z-Anatomy** (template Blender `Startup.blend`, dépôt GitHub `Z-Anatomy/Models-of-human-anatomy`, fichier daté du 2 mai 2023).

## Licences

- **Z-Anatomy** — Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).  
  https://creativecommons.org/licenses/by-sa/4.0/  
  Auteurs : Gauthier Kervyn (design, 3D, anatomie), Marcin Zielinski (script Blender).  
  Dépôt : https://github.com/Z-Anatomy/Models-of-human-anatomy

- **BodyParts3D** — les modèles Z-Anatomy en sont dérivés.  
  Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP).  
  « BodyParts3D, Copyright© The Database Center for Life Science licensed by CC Attribution-Share Alike 2.1 Japan. »  
  https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html

Toute redistribution de ces GLB doit rester sous **CC BY-SA 4.0** (compatible avec le share-alike de BodyParts3D). Le code de cet essai (scripts, page de comparaison) est fourni avec le dépôt ; les maillages restent sous CC BY-SA.

## Ce qui a été modifié

Extraction des quatre muscles de la paroi (gauche et droite), soudure des sommets éclatés, normales lissées, décimation (meshoptimizer et Blender Decimate), cartes de normales tangentes optionnelles. La gaine des droits n’existe pas comme objet séparé dans la source : seule une matière « Tendon » est peinte sur le droit de l’abdomen.
