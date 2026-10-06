# Notes pédagogiques — lignes type « Anatomy Trains »

**Statut :** implémenté dans l’UI (Couches → Chaînes myofaciales) via `src/data/chains.json`. Données pédagogiques originales, sans extraits d’ouvrage.

## Avertissement

Ces notes décrivent un **modèle pédagogique** de continuités myofasciales popularisé par **Thomas W. Myers** sous le nom *Anatomy Trains*. Ce n’est **pas** une vérité anatomique unique, ni un protocole clinique.

Les fascias, les muscles et les variations individuelles sont plus complexes que des « lignes » dessinées. Utiliser ce cadre comme **outil de lecture** (orientation, compensation, enseigner des chaînes de mouvement), pas comme carte exclusive du corps.

Aucun extrait d’ouvrage protégé n’est reproduit ici. Pour le détail des stations, des dissections et des protocoles, se reporter aux publications officielles de l’auteur et aux éditeurs concernés.

**Concept cité :** Tom Myers, *Anatomy Trains* (myofascial meridians).

## Idée générale (reformulation originale)

On peut relier certains muscles et septums fascials en **continuités mécaniques** longues, de la voûte plantaire au crâne (ou de la main au tronc). Une tension ou une restriction à un maillon peut se lire plus loin sur la même continuité — hypothèse d’enseignement, à confronter à la clinique et à l’imagerie.

## Lignes souvent enseignées (noms usuels)

Abréviations anglaises conservées car c’est le vocabulaire de terrain ; traductions libres entre parenthèses.

| Sigle | Nom usuel | Lecture pédagogique (très courte) |
| --- | --- | --- |
| **SBL** | Superficial Back Line (ligne superficielle postérieure) | Continuité postérieure, de la plante vers la nuque / le crâne ; souvent associée à l’extension et au maintien « en arrière ». |
| **SFL** | Superficial Front Line (ligne superficielle antérieure) | Continuité antérieure, de la face dorsale du pied / jambe vers le tronc et le cou ; souvent associée à la flexion. |
| **LL** | Lateral Line (ligne latérale) | Étriers latéraux, malléoles / hanche / tronc / cou ; stabilité frontale, inclinaisons. |
| **SPL** | Spiral Line (ligne spirale) | Croix et hélices autour du tronc et des membres ; rotations et contre-rotations. |
| **DFL** | Deep Front Line (ligne profonde antérieure) | Axe profond (cou, thorax, psoas, jambe profonde) ; appui, respiration, organisation du centre. |
| **Lignes du bras** | Superficial / Deep Front & Back Arm Lines | Continuités de la ceinture scapulaire vers le pouce / les doigts (faces antérieures et postérieures, superficielles et profondes). |
| **Lignes fonctionnelles** | Front / Back Functional Lines, ligne ipsilatérale | Ponts tronc–membre controlatéral ou homolatéral dans les gestes de lancer, de foulée, de transfert. |

Les noms exacts des « stations » (os, muscles, septums) relèvent de l’ouvrage et des formations : **ne pas les recopier** dans le code ou la doc produit sans source libre ou autorisation.

## Pistes d’implémentation (Phase 2 seulement)

- Fichier de données distinct, p. ex. `src/data/chains.json`, avec `id`, `sigle`, `nom`, `muscleIds[]`.
- Affichage : teinte de chaîne + muscles déjà connus de Phase 1, **sans** remplacer le mode « un muscle ».
- Toujours afficher le disclaimer pédagogique dans l’UI de Phase 2.

## Références conceptuelles (non exhaustif)

- Myers, T. W. — *Anatomy Trains* (concept de méridiens myofasciaux).
- Travaux d’anatomie fasciale contemporaine (contexte scientifique plus large que le modèle des lignes).
