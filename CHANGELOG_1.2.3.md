# FoxCat Energy 1.2.3 — 13/09/2026

Statut : **À TESTER**.

## Correction — cycle machine protégé et boiler

Un cycle machine protégé ne bloque plus automatiquement le chauffe-eau.

Nouvelle règle :
- la machine déjà en cycle reste prioritaire et n'est jamais interrompue ;
- le chauffe-eau peut démarrer ou continuer si le surplus solaire réellement disponible **après la consommation de la machine** couvre la puissance nominale configurée du chauffe-eau ;
- si le chauffe-eau est déjà ON, FoxCat reconstitue le surplus avant chauffe en ajoutant sa puissance mesurée à la balance réseau ;
- si le surplus devient insuffisant pendant un cycle protégé, FoxCat arrête le chauffe-eau, sauf en mode Manuel où FoxCat ne reprend pas la main ;
- aucune règle de sécurité thermique n'est supprimée.

Cette garde est centralisée dans le CORE afin d'être cohérente entre Économie énergie, ECS solaire et Prix dynamique.

Deux nouvelles entités de diagnostic sont ajoutées :
- `binary_sensor.*boiler_autorise_cycle_protege` ;
- `sensor.*surplus_disponible_boiler_cycle_protege`.

## Ajout — prix HP/HC fournis par des entités Home Assistant

Dans **Reconfigurer → Tarifs HP/HC**, l'utilisateur peut maintenant sélectionner :
- une entité pour le prix HP ;
- une entité pour le prix HC ;
- facultativement une entité pour le prix fixe de réinjection.

Les valeurs manuelles restent disponibles comme secours. Une valeur d'entité valide est prioritaire ; si l'entité est absente/indisponible/non numérique, FoxCat reprend la valeur manuelle configurée.

Trois capteurs de diagnostic indiquent la source actuellement utilisée :
- Source prix heures pleines ;
- Source prix heures creuses ;
- Source prix fixe de réinjection.

## Architecture future — appareils extensibles

Préparation fonctionnelle retenue pour une version ultérieure : passer d'une liste fixe d'appareils à des profils déclaratifs basés sur leurs capacités, par exemple :
- charge ON/OFF ;
- cycle protégé ;
- stockage thermique ;
- batterie / charge variable ;
- puissance mesurée ;
- puissance pilotable ;
- état de charge / SOC ;
- autorisation réseau ;
- priorité EMS ;
- contraintes horaires.

Cette partie n'est **pas encore activée** dans 1.2.3 afin de ne pas introduire un faux support de batteries ou de multiples boilers sans arbitre énergétique dédié.
