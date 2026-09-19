# FoxCat Energy 1.4.0 — Coûts & Bilan énergétique

- Nouveau moteur `accounting/`, strictement observateur : aucune influence sur les décisions EMS.
- Comptabilisation à partir des trames valides : maison, PV, autoconsommation, import, export.
- Autoconsommation %, autonomie %, coût réseau, valeur de réinjection, coût net, gain solaire estimé.
- Cumuls aujourd'hui / mois / année / durée de vie.
- Tarification appliquée trame par trame via le prix actif FoxCat (dynamique, HP/HC ou compensation).
- Comptabilité automatique du chauffe-eau et des machines possédant un capteur de puissance.
- Estimation par appareil : énergie, part solaire, part réseau et coût réseau.
- Les resets Smappee, trous >90 s et redémarrages HA ne sont jamais intégrés comme de l'énergie.
- Sauvegarde persistante périodique toutes les 5 minutes.
- PRI classique 1.3.203 inchangé.
