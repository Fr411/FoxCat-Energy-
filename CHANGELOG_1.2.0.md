# FoxCat Energy — Changelog 1.2.0

Statut : **À TESTER**.

## Correctifs

- Correction du flux **Reconfigurer** : suppression de la mise à jour/reload du `ConfigEntry` pendant que l'OptionsFlow est encore ouvert.
- Adoption du modèle Home Assistant récent : `OptionsFlow` récupère `self.config_entry` automatiquement.
- Les modifications de reconfiguration sont maintenant transactionnelles et enregistrées une seule fois avec **Enregistrer et quitter**.
- Le coordinator fusionne désormais `entry.data` et `entry.options`.

## Modes EMS

- Suppression de **Confort**.
- Migration d'un ancien état `Confort` vers **Manuel**.
- **Économie énergie** devient hybride : boiler + stockage solaire utile + PRI zéro injection sur l'excédent résiduel.
- **ECS solaire** conserve sa logique métier de référence.
- **Zéro injection** pilote le PRI sur la réinjection réseau réelle et non sur la consommation maison.
- **Manuel** devient un vrai handover : pas de stratégie boiler, pas de PRI automatique, pas de planning automatique machines ; sécurité thermique conservée.
- Ajout d'un sélecteur **Niveau PRI manuel** 0–100 % par pas de 10 %.

## PRI zéro injection

- Une marche de 10 % n'est plus appliquée si elle transformerait un petit export en prélèvement supérieur à la tolérance.
- Distinction comportementale entre zéro total et zéro partiel stable.
- Remontée anti-oscillation : refus si la marche supérieure recréerait trop d'export.
- Temporisation configurable du PRI après une action boiler (`pri_boiler_settle_s`, 30 s par défaut).

## Prix dynamique

- Le mode exige désormais **Régime tarifaire = Dynamique** ; sinon la stratégie est bloquée et le PRI est libéré à 100 %.
- Réévaluation immédiate lors d'un changement de capteur de prix.
- Analyse conservée : prix actuel, prix suivant, min, max, moyenne et prix d'injection.
- **Nouveau : charge réseau sur prix négatif.** Si le prix d'achat dynamique est inférieur au seuil configuré (0 €/kWh par défaut), FoxCat peut commander `BOOST_65` et charger le boiler sur le réseau jusqu'à 65 °C.
- Nouveau switch : **Charge réseau si prix dynamique négatif**.
- Nouveau réglage : **Seuil charge réseau prix négatif**.
- La sécurité 68 °C et la priorité machine restent souveraines.

## Tarification

- Nouveau sélecteur **Régime tarifaire** : Compensation / Bi-horaire HP/HC / Dynamique.
- Nouvelles plages HP configurables avec valeurs AIESH par défaut 07–11 et 17–22.
- Nouveaux réglages : prix achat HP, prix achat HC, prix fixe de réinjection.
- Nouveaux capteurs : période tarifaire, statut prix, prix achat actif, valeur économique de réinjection, coût instantané import, valeur instantanée export et solde financier instantané.
- Sous compensation, le modèle de coût est explicitement marqué `ESTIMATION_COMPENSATION`.

## Structure Python

Les stratégies ont été séparées dans `engine/modes/` :

- `eco.py`
- `ecs_solar.py`
- `zero_injection.py`
- `dynamic.py`
- `manual.py`
- `common.py`

`engine/strategies.py` reste comme shim de compatibilité.

## Fichiers modifiés par rapport à 1.1.0

- `custom_components/foxcat_energy/manifest.json`
- `custom_components/foxcat_energy/const.py`
- `custom_components/foxcat_energy/config_flow.py`
- `custom_components/foxcat_energy/coordinator.py`
- `custom_components/foxcat_energy/select.py`
- `custom_components/foxcat_energy/number.py`
- `custom_components/foxcat_energy/switch.py`
- `custom_components/foxcat_energy/sensor.py`
- `custom_components/foxcat_energy/strings.json`
- `custom_components/foxcat_energy/translations/fr.json`
- `custom_components/foxcat_energy/engine/__init__.py`
- `custom_components/foxcat_energy/engine/pri.py`
- `custom_components/foxcat_energy/engine/strategies.py`
- `custom_components/foxcat_energy/engine/tariff.py`

## Fichiers ajoutés

- `custom_components/foxcat_energy/engine/modes/__init__.py`
- `custom_components/foxcat_energy/engine/modes/common.py`
- `custom_components/foxcat_energy/engine/modes/eco.py`
- `custom_components/foxcat_energy/engine/modes/ecs_solar.py`
- `custom_components/foxcat_energy/engine/modes/zero_injection.py`
- `custom_components/foxcat_energy/engine/modes/dynamic.py`
- `custom_components/foxcat_energy/engine/modes/manual.py`
- `MIGRATION_1.1.0_to_1.2.0.md`

## Tests exécutés hors Home Assistant

- compilation Python de tous les modules ;
- validation JSON `manifest.json`, `strings.json`, `translations/fr.json`, `hacs.json` ;
- tests purs du moteur PRI : descente sur export fort, zéro partiel anti-oscillation, remontée sur import ;
- test du mode dynamique : prix négatif → `BOOST_65` ;
- test de désactivation de la charge prix négatif ;
- test de blocage du mode Prix dynamique avec régime Compensation ;
- test du mode Économie énergie : surplus solaire → 45 °C puis boost 65 °C.

Le comportement physique réel reste **À TESTER** sur Home Assistant / SolarEdge / boiler.
