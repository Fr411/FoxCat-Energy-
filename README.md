# FoxCat Energy 1.2.2

Custom component Home Assistant pour l'EMS FoxCat Energy. Cette version restructure les modes EMS, corrige la reconfiguration, renforce le PRI zéro injection et ajoute un véritable contexte tarifaire.

**Statut : À TESTER sur installation réelle avant validation.**

## Important avant activation

L'intégration conserve **Régulation FoxCat active = OFF** lors d'une première installation. Elle peut ainsi être observée avant de lui donner le contrôle physique.

1. Installer `custom_components/foxcat_energy` dans `/config/custom_components/` ou mettre à jour via HACS.
2. Redémarrer complètement Home Assistant.
3. Ouvrir **Paramètres → Appareils et services → FoxCat Energy**.
4. Vérifier les associations d'entités et la section **Tarification**.
5. Désactiver les anciennes automatisations qui commandent directement boiler / PRI / machines avant d'activer la régulation FoxCat.

FoxCat ne supprime pas les anciens helpers ni les anciennes automatisations.

## Nouveau en V1.2.2 — page Tarifs HP/HC

La reconfiguration sépare maintenant **Tarification dynamique** et **Tarifs HP/HC**.
Dans **Reconfigurer → Tarifs HP/HC**, l’utilisateur peut saisir directement :

- le prix d’achat heures pleines (HP) en €/kWh TVAC ;
- le prix d’achat heures creuses (HC) en €/kWh TVAC ;
- le prix fixe de réinjection ;
- les deux plages horaires HP.

FoxCat expose aussi trois capteurs dédiés sur le device **Tarification** : **Prix heures pleines (HP)**, **Prix heures creuses (HC)** et **Prix fixe de réinjection**. Les anciens `number` de réglage restent présents pour compatibilité et sont synchronisés avec la configuration.

## Reconfiguration V1.2.0

Le flux **Reconfigurer** a été rendu transactionnel : les modifications restent locales tant que l'utilisateur n'a pas choisi **Enregistrer et quitter**. Le `ConfigEntry` n'est plus rechargé au milieu du flux, ce qui évite le `500 Internal Server Error` observé en V1.1.0.

Les options modifiées sont stockées dans `entry.options`; la configuration effective est `entry.data + entry.options`.

## Architecture des modes EMS

La V1.2.0 conserve cinq modes :

### Économie énergie

Mode hybride :

- pilote le boiler ;
- utilise le surplus solaire utile avant bridage ;
- permet un stockage opportuniste jusqu'à 65 °C lorsque le boiler est couvert par le solaire ;
- conserve le confort minimal 45 °C en HC ;
- interdit l'achat volontaire du boiler en HP ;
- pilote aussi le PRI sur le surplus résiduel avec la logique zéro injection réseau ;
- temporise le PRI après une action boiler afin de laisser le réseau se stabiliser.

### ECS solaire

La logique métier de la V1.1 est conservée : cycle minimum, failback thermique, HC jour/nuit, HP sans achat volontaire, transition 45 → 65 et boost solaire. Le PRI automatique est libéré à 100 %.

### Zéro injection

Le PRI est piloté par la **réinjection réseau réelle**. La consommation maison n'est plus une cible de commande et reste seulement un diagnostic.

FoxCat recherche :

- un zéro total si une marche RRCR de 10 % le permet sans import excessif ;
- un zéro partiel stable si la granularité de 400 W rend le zéro exact impossible ;
- une remontée uniquement si elle ne recrée pas une réinjection excessive ;
- un rollback si une remontée réelle produit trop d'export.

### Prix dynamique

Le mode n'est autorisé que si **Régime tarifaire = Dynamique**.

Il analyse :

- prix actuel ;
- prix suivant ;
- minimum / maximum / moyenne du jour ;
- prix de réinjection dynamique ;
- potentiel solaire ;
- état thermique du boiler.

Priorités : sécurité → machines protégées → prix négatif → solaire utile → arbitrage financier min/max/tendance.

#### Charge réseau lorsque le prix devient négatif

Nouveau en V1.2.0 : si le prix d'achat dynamique devient **strictement inférieur au seuil configuré** (0 €/kWh par défaut), FoxCat est autorisé à tirer sur le réseau et à charger le boiler jusqu'à la cible de stockage 65 °C, sous réserve des sécurités et priorités machines.

Entités associées :

- **Charge réseau si prix dynamique négatif** : activation / désactivation ;
- **Seuil charge réseau prix négatif** : 0 €/kWh par défaut ;
- **Prix dynamique négatif actif** : état diagnostique.

Le solaire reste prioritaire hors ce cas financier explicite. Le PRI tient en parallèle compte de la valeur de réinjection : injection intéressante → libération progressive ; injection défavorable → limitation de l'excédent.

### Manuel

Handover complet :

- aucune stratégie boiler automatique ;
- aucun PRI automatique ;
- aucun planning automatique des prises machines ;
- l'utilisateur pilote directement le climate boiler et les prises ;
- un sélecteur **Niveau PRI manuel** permet 0 / 10 / … / 100 % ;
- la sécurité thermique dure reste active.

Lors de l'entrée en Manuel, le PRI est d'abord remis à 100 % comme état sûr, puis l'utilisateur reprend la main.

### Suppression du mode Confort

Le mode **Confort** disparaît de la liste. Une installation V1.1 enregistrée sur `Confort` est migrée prudemment vers **Manuel** afin de ne lancer aucune stratégie automatique sans choix explicite.

## Régime tarifaire indépendant du mode EMS

Nouvelle entité : **Régime tarifaire**.

Valeurs :

- `Compensation`
- `Bi-horaire HP/HC`
- `Dynamique`

Le mode EMS décrit **comment FoxCat agit** ; le régime tarifaire décrit **comment l'énergie est facturée**.

Le mode **Prix dynamique** est bloqué si le régime n'est pas `Dynamique`.

## Tarification HP / HC

Les deux plages HP sont configurables dans **Reconfigurer → Tarification**. Valeurs AIESH par défaut :

- HP1 : 07:00 → 11:00
- HP2 : 17:00 → 22:00
- HC : le reste

Entités `number` de tarification :

- **Prix achat heures pleines** ;
- **Prix achat heures creuses** ;
- **Prix fixe de réinjection**.

Les valeurs de prix sont laissées à 0 par défaut afin de ne pas inventer le contrat du client ; le statut indique **PRIX À CONFIGURER** tant qu'elles ne sont pas renseignées.

## Statut prix et coûts

Le device **FoxCat Energy – Tarification** expose notamment :

- régime tarifaire actif ;
- période HP / HC ;
- statut du prix (`NÉGATIF`, `TRÈS BAS`, `BAS`, `NORMAL`, `ÉLEVÉ`, `TRÈS ÉLEVÉ`) ;
- prix d'achat actif ;
- valeur économique normalisée de la réinjection ;
- coût instantané du prélèvement en €/h ;
- valeur instantanée de la réinjection en €/h ;
- solde financier instantané réseau en €/h.

Sous compensation, le modèle est explicitement identifié comme **ESTIMATION_COMPENSATION** : un coût instantané ne remplace pas le décompte annuel de compensation.

## Contrat énergétique

- Production PV : positive en W.
- Consommation maison : positive en W.
- Réinjection réseau : positive en W.
- Prélèvement réseau : positif en W.
- `balance réseau = réinjection - prélèvement`.

Le PRI zéro injection utilise le réseau physique comme arbitre. `sensor.consommation_reelle_maison` reste disponible pour diagnostic mais ne pilote plus directement le niveau RRCR en Zéro injection.

## PRI SolarEdge RRCR

Table L4 L3 L2 L1 :

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

Une décision normale ne change qu'une marche de 10 %, puis attend les ACK RRCR / onduleur / réseau.

## EMS Machines

Chaque machine conserve deux plages ON/OFF configurables. Un cycle déjà commencé n'est jamais interrompu en mode automatique.

En **Manuel**, FoxCat ne commande plus les prises : l'utilisateur gère chaque machine directement.

## Structure moteur V1.2.0

Les stratégies sont maintenant séparées :

```text
engine/
├── pri.py
├── tariff.py
└── modes/
    ├── common.py
    ├── eco.py
    ├── ecs_solar.py
    ├── zero_injection.py
    ├── dynamic.py
    └── manual.py
```

`engine/strategies.py` reste comme shim de compatibilité vers le nouveau routeur de modes.

## Retour arrière

Pour revenir immédiatement à l'ancien système :

1. mettre **Régulation FoxCat active** sur OFF ;
2. utiliser **Libérer l'onduleur à 100 %** si nécessaire ;
3. réactiver les anciennes automatisations ou réinstaller la V1.1.0.
