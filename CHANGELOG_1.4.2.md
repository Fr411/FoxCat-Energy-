# FoxCat Energy 1.4.2

## Configuration Home Assistant — Coûts & Bilan

La comptabilité énergétique est maintenant regroupée dans un seul appareil :

`FoxCat Energy – Coûts & Bilan`

Les anciens appareils comptables séparés (Maison totale, Photovoltaïque,
Chauffe-eau et appareils mesurés) ne sont plus créés par FoxCat 1.4.2.

Les entités sont classées visuellement par préfixes :

- 🏠 Maison • ...
- ☀️ PV • ...
- 🔌 Chauffe-eau • ...
- 🔌 Lave-vaisselle • ...
- 🔌 Toute autre machine mesurée • ...

Home Assistant ne proposant pas de séparateurs arbitraires dans la page native
d'un appareil, ces préfixes servent de séparateurs visuels sans créer de fausses
entités.

## Inchangé
- Calculs Coûts & Bilan 1.4.0
- CORE EMS
- PRI classique
- Tarification
- Gestion reset Smappee
- Cycles protégés
- Délestage
