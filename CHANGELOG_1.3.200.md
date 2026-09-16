# FoxCat Energy 1.3.200

## Architecture
- `sensor.consommation_reelle_maison` devient l'horloge souveraine du CORE.
- Une décision énergétique complète au maximum par nouvelle trame (~30 s).
- ACK PRI validé sur la trame N+1, plus sur `sleep(30)`.

## PRI
- Nouveau régulateur PI discret, anti-windup, sortie quantifiée par pas RRCR de 10 %.
- Consigne réseau par défaut : +75 W d'export.
- Comparateur PRI/PV : PV_LIMITED, PV_BELOW_LIMIT, PRI_INCONSISTENT, PV_UNKNOWN.
- Une production bridée n'est plus utilisée pour conclure à une fin solaire.

## Charges
- Les cycles machines protégés restent prioritaires et ne sont jamais coupés par le délestage.
- Boiler compatible avec cycle protégé si le surplus vérifié est suffisant.

## Délestage
- 2 trames hautes consécutives pour déclencher.
- 5 trames basses consécutives pour réarmer.
- Une consommation maison unavailable/unknown gèle l'état au lieu d'être assimilée à 0 W.

## Statut
Version expérimentale à valider sur Home Assistant réel et par simulation 100 000 trames avant promotion stable.
