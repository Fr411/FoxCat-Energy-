# FoxCat Energy 1.3.201

## Correctif PRI
- Correction du verrou qui pouvait empêcher l'exécution du PRI lorsque la production PV mesurée était faible après bridage.
- La puissance PV brute n'est plus utilisée dans `_pri_guard()` pour interdire le moteur PRI.
- La trame `consommation_reelle_maison` reste l'horloge souveraine du CORE.
- Le changement du capteur réseau reste de la télémétrie : aucune seconde boucle PRI concurrente n'est réintroduite.
- Le comparateur PRI/PV et la validation de commande sur N+1 sont conservés.
- Diagnostic explicite lorsque le PRI attend la trame N+1.

## Inchangé
- Régulateur PRI-PI.
- Pas RRCR de 10 %.
- Anti-windup.
- Cycles machines protégés.
- Délestage 2 trames hautes / 5 trames basses.
- Protection contre les fausses fins solaires.
