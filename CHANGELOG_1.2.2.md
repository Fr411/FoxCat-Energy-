# FoxCat Energy 1.2.2 — Tarifs HP/HC

Statut : **À TESTER**

## Ajouts

- nouvelle page de configuration/reconfiguration **Tarifs HP/HC** ;
- saisie du prix HP, du prix HC et du prix fixe de réinjection ;
- plages HP 1 et 2 regroupées sur cette page ;
- nouveaux capteurs : **Prix heures pleines (HP)**, **Prix heures creuses (HC)** et **Prix fixe de réinjection** ;
- migration douce : les valeurs V1.2.1 déjà réglées via les entités `number` sont proposées sur la nouvelle page ;
- les entités `number` existantes sont conservées et synchronisées vers la configuration pour éviter toute régression.

## Inchangé

- stratégies EMS ;
- logique PRI ;
- ECS solaire ;
- mode dynamique et charge réseau à prix négatif ;
- gestion machines ;
- sécurités et ACK.
