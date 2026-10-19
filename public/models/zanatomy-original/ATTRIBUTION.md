# Attribution — Z-Anatomy, corps entier, résolution d’origine

Fichiers : `public/models/zanatomy-original/*.glb` et `manifest.json`.

Export du modèle **Z-Anatomy** (template Blender `Startup.blend`, 2 mai 2023) pour comparer la qualité brute du maillage, sans le décimer. Page : `zanatomy.html`.

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

Toute redistribution de ces GLB doit rester sous **CC BY-SA 4.0**. Le code de l’application (MIT) est distinct du maillage.

## Ce qui a été modifié

- Un GLB par système : squelette (os et cartilages, y compris disques, ménisques et labrums des articulations), muscles, fascias (fascias d’enveloppe, aponévroses de surface, bandelette ilio-tibiale, gaines tendineuses, bourses, rétinaculums — décochés par défaut), ligaments (capsules et membranes interosseuses), nerfs (encéphale, organes des sens et nerfs périphériques), vaisseaux, organes (viscères, organes lymphoïdes et cœur).
- Les muscles gardent leur géométrie d’origine. La couleur est un rouge de fibre, les fentes tendineuses restent pâles. Le tenseur du fascia lata, le long palmaire et les interosseux restent dans les muscles.
- Les repères d’insertion (collection « Muscular insertions »), les libellés (`.g`, `.j`, `.t`), les régions de surface et la collection bonus ne sont pas exportés.
- Matrices monde figées, côté gauche (déterminant négatif) avec normales inversées, export Y-up. Origine Z-Anatomy vers les pieds — **pas** aligné sur le squelette de l’application.
- Les modificateurs qui construisent la forme (miroir, solidify, skin, subdivision au niveau d’affichage, booléens, biseau des courbes) sont évalués. Le modificateur Decimate (un objet) et les wireframes sont ignorés. Aucune décimation supplémentaire.
- Compression **Draco** seule : edgebreaker, positions **16 bits**, normales 10 bits, coordonnées de texture 12 bits.
- Couleurs par système (os ivoire, cartilage bleu-gris, muscle rouge, tendon clair, ligament crème, nerf or, artère rouge, veine bleue, organe rose). Les noms d’objets restent ceux de Z-Anatomy (anglais).

Les comptes de triangles et les tailles sont dans `manifest.json`.
