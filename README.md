# FoxCat Energy 1.1.0

Custom component Home Assistant destiné à encapsuler l'EMS FoxCat fourni dans les automatisations de référence : CORE V8.2, ECS solaire V1.7, Prix dynamique V1, EMS 2 prédictif, vérificateur souverain d'exécution et PRI V3.0.

## Important avant activation

L'intégration s'installe avec **Régulation FoxCat active = OFF**. Elle commence donc en télémétrie uniquement. Cela évite qu'elle commande en même temps que les anciennes automatisations.

1. Installer le dossier `custom_components/foxcat_energy` dans `/config/custom_components/`.
2. Redémarrer Home Assistant.
3. Aller dans **Paramètres → Appareils et services → Ajouter une intégration → FoxCat Energy**.
4. Vérifier les entités proposées dans les six étapes de configuration.
5. Vérifier les capteurs FoxCat créés et lancer **Lancer un diagnostic EMS**.
6. Désactiver les anciennes automatisations qui commandent le boiler, les prises ou le PRI avant de passer la nouvelle entité **Régulation FoxCat active** sur ON.

L'intégration ne supprime, ne désactive et ne modifie automatiquement aucune ancienne automatisation ou helper.

## Contrat énergétique

- Production PV : valeur positive en W.
- Consommation maison : valeur positive en W.
- Réinjection compteur : valeur positive en W.
- Prélèvement compteur : valeur positive en W.
- `balance réseau = réinjection - prélèvement`.
- L'ancien capteur signé `sensor.retourne_au_reseau` est conservé uniquement comme champ de compatibilité et n'est pas utilisé comme vérité réseau par le moteur Python.

## Migration contrôlée

- La régulation est **OFF par défaut**.
- En sélectionnant **Économie énergie**, **Zéro injection** ou **Prix dynamique**, le switch logiciel PRI est armé automatiquement.
- En quittant ces modes, le PRI est désarmé et, si la régulation est active, l'onduleur est libéré à 100 %.
- Le compteur de cycle boiler est volontairement conservateur : seul `binary_sensor.boiler` fait foi pour la durée physique ; si de la puissance est détectée sans binaire ON, la durée connue vaut 0 s.

## Modes

### Économie énergie
- Boiler : chauffe 45 °C en HC si nécessaire.
- Aucun achat volontaire du boiler en HP.
- PRI : moteur universel zéro réinjection.
- Machines : deux plages horaires configurables par machine depuis l’onglet EMS Machines (valeurs par défaut 21:30–07:00 et 10:30–17:00), cycles protégés.

### Zéro injection
- Moteur PRI universel actif.
- Pas de stratégie boiler propre au mode.
- Le PRI est piloté directement par la réinjection réseau : si l’export dépasse le seuil acceptable, FoxCat descend d’une marche de 10 %. La consommation maison reste uniquement un repère diagnostique et ne commande plus le niveau PRI.

### ECS solaire
- Stratégie V1.7 : observation nocturne, charge initiale, stabilisation, failback thermique, HC jour, HP sans achat réseau volontaire, cycle minimum, transition 45 → 65 sans coupure, boost solaire.
- PRI automatique libéré à 100 %.

### Prix dynamique
- Utilise les capteurs Luminus Dynamic configurés.
- Priorité solaire, attente tarifaire, créneaux bas, garantie thermique, stockage solaire 65 °C si pertinent.
- PRI dynamique : injection rémunératrice = libération vers 100 %. Injection défavorable = réduction d'une marche seulement si elle ne projette pas volontairement un import réseau.
- Le réseau est calculé depuis les deux capteurs physiques compteur, pas depuis `PV - maison`.

### Confort
Le corpus fourni mentionnait ce mode mais ne contenait pas de stratégie dédiée. Pour rendre le composant complet, l'implémentation V1 garantit simplement 45 °C lorsque la température descend sous le seuil de reprise, avec les sécurités thermiques et machines toujours prioritaires. Le PRI automatique reste libéré.

### Manuel
Aucune stratégie automatique boiler/PRI. Les sécurités thermiques et la protection des machines restent actives. La gestion indépendante des prises machines reste active, comme dans l'architecture actuelle.

## CORE souverain

Le CORE suit une machine d'état :

`ACQUISITION → DECISION → WAIT_ACK → ACQUISITION`

`sensor.consommation_reelle_maison` est la seule horloge énergétique du CORE. Une trame mémorise T0, la suivante décide au maximum une action significative, et la trame suivante valide l'ACK réseau.

## PRI SolarEdge

Le moteur PRI est séparé du CORE chauffe-eau. En Zéro injection, la mesure réseau est l’arbitre :

1. lecture de la réinjection/prélèvement ;
2. décision sur le flux réseau réel ;
3. une seule marche de 10 % ;
4. ACK RRCR ;
5. validation onduleur et réseau ;
6. nouvelle correction uniquement si la réinjection ou le prélèvement reste hors zone.

Table RRCR L4 L3 L2 L1 :

| Niveau | Code |
|---:|:---:|
| 100 % | 0000 |
| 90 % | 1001 |
| 80 % | 1000 |
| 70 % | 0111 |
| 60 % | 0110 |
| 50 % | 0101 |
| 40 % | 0100 |
| 30 % | 0011 |
| 20 % | 0010 |
| 10 % | 0001 |
| 0 % | 1010 |

Le moteur peut accepter un petit import ou un petit export. Par défaut : export idéal ≤ 50 W, import idéal ≤ 100 W, export acceptable ≤ 150 W et import acceptable ≤ 200 W. Les valeurs sont modifiables depuis les entités `number` créées par l'intégration.

## Fin solaire

En modes Économie énergie et Zéro injection, si la production PV reste sous 5 W pendant 180 secondes, FoxCat :

- libère l'onduleur à 100 % ;
- annule le cycle PRI ;
- bascule automatiquement le mode EMS vers **ECS solaire**.

Les deux seuils sont réglables.

## EMS 2

EMS 2 reste purement prédictif. Il s'exécute à 07:00, 10:30, 11:00, 15:00, 17:00 et 22:00 ainsi qu'avec le bouton **Analyser la prévision solaire**.

Si une entité `ai_task` est configurée, l'intégration appelle `ai_task.generate_data` avec une sortie structurée. Si le service n'est pas disponible ou échoue, un fallback local conservateur produit quand même un état consultatif à partir des capteurs Forecast.Solar.

## Migration des anciens helpers

Au tout premier démarrage, si les anciens helpers existent encore, FoxCat importe leurs valeurs pour les températures, tolérances, seuils, autorisations et mode EMS. Le switch maître **Régulation FoxCat active** n'est jamais activé automatiquement.

## Entités principales créées

- `select.foxcat_energy_mode_ems`
- `switch.foxcat_energy_regulation_foxcat_active`
- `switch.foxcat_energy_reduction_de_puissance_onduleur`
- `switch.foxcat_energy_boiler_gere_par_foxcat`
- capteurs CORE/ACK/PRI/réseau/boiler/EMS 2
- réglages `number` en français
- boutons diagnostic, reset, analyse solaire, libération onduleur et réconciliation machines

Les entity_id exacts peuvent être suffixés par Home Assistant en cas de conflit avec une entité existante ; les `unique_id` restent stables.

## Retour arrière

Pour revenir immédiatement à l'ancien système :

1. mettre **Régulation FoxCat active** sur OFF ;
2. utiliser **Libérer l'onduleur à 100 %** si nécessaire ;
3. réactiver les anciennes automatisations.

Aucun helper ou YAML historique n'est supprimé par l'intégration.
