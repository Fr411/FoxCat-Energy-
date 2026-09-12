# FoxCat Energy 1.2.1 — correctif ConfigFlow

Statut : **À TESTER**.

## Correctif principal

- Corrige le cas où Home Assistant affiche `Invalid handler specified` lors du chargement du flux de configuration.
- `custom_components/foxcat_energy/__init__.py` n'importe plus le coordinator au chargement du package : le coordinator est importé seulement lors de `async_setup_entry()`.
- `config_flow.py` ne construit plus tous les sélecteurs et schémas à l'import du module. Les schémas sont créés au moment où l'étape correspondante est réellement ouverte.
- Remplacement de `from .const import *` par des imports explicites.
- Le flux d'options reste transactionnel : aucune mutation du ConfigEntry pendant que le menu de reconfiguration est ouvert ; un seul commit à « Enregistrer et quitter ».

## Comportement énergétique

Aucun changement fonctionnel du moteur EMS 1.2.0 : modes, PRI, boiler, machines, tarification dynamique et charge réseau à prix négatif restent inchangés.
