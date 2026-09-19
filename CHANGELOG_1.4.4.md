# FoxCat Energy 1.4.4 — Horloge EMS/PRI 30 secondes

## Correction principale
Le moteur EMS/PRI n'est plus dépendant d'un changement d'état du capteur
`Consommation réelle maison`.

FoxCat possède maintenant une horloge unique :
- tick à `xx:02`
- tick à `xx:32`
- soit exactement une exécution toutes les 30 secondes.

Le décalage de 2 secondes laisse aux capteurs physiques configurés sur 30 s le
temps de publier leur trame avant la décision FoxCat.

À CHAQUE tick valide :
1. acquisition PV / maison / réseau ;
2. validation éventuelle de la commande PRI N+1 précédente ;
3. délestage haute consommation ;
4. CORE boiler/machines ;
5. calcul PRI ;
6. commande RRCR de ±10 % maximum ;
7. attente du tick suivant pour validation.

Les événements PV/réseau continuent de rafraîchir la télémétrie, mais ils ne
peuvent plus provoquer plusieurs décisions PRI entre deux ticks.

## Conservé
- PRI hybride 1.4.3 ;
- priorité import réseau ;
- correction export ;
- comparateur PV/plafond PRI ;
- ACK RRCR et validation N+1 ;
- reset Smappee ;
- cycles protégés ;
- priorité utilisateur ;
- délestage ;
- Coûts & Bilan.
