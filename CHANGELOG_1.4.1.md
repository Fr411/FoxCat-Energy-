# FoxCat Energy 1.4.1

## Organisation Coûts & Bilan dans Home Assistant
Les entités comptables sont maintenant classées dans des appareils distincts :

- `FoxCat Energy – Maison totale`
  - consommation maison
  - prélèvement réseau
  - coût réseau
  - coût énergétique net
  - autonomie

- `FoxCat Energy – Photovoltaïque`
  - production PV
  - PV autoconsommé
  - réinjection
  - taux d'autoconsommation
  - valeur de réinjection
  - gain solaire

- `FoxCat Energy – Chauffe-eau`
  - énergie
  - part solaire
  - part réseau
  - coût

- Chaque machine FoxCat disposant d'un capteur de puissance obtient automatiquement
  son propre appareil Home Assistant avec ses capteurs énergie/solaire/réseau/coût.

## Inchangé
- Moteur de comptabilité 1.4.0.
- PRI classique.
- CORE EMS.
- Gestion reset Smappee.
- Machines protégées et délestage.
