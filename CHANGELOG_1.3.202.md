# FoxCat Energy 1.3.202

## Reset Smappee / trames
- Les états `unknown` / `unavailable` pendant le reset périodique Smappee ne sont plus considérés comme des trames EMS.
- `frame_id` n'avance que sur une trame énergétique complète et valide.
- L'ACK PRI N+1 attend une vraie trame valide.
- L'intégrale PI est gelée pendant l'indisponibilité.
- Le niveau PRI est conservé.
- Le délestage actif est conservé et ses compteurs ne progressent pas sur les données invalides.
- Les cycles protégés ne sont pas interrompus par une indisponibilité de mesure.
- Après le retour des capteurs, une première trame valide sert uniquement à la stabilisation ; les décisions reprennent sur la suivante.

## Diagnostic PRI
- `_pri_guard()` expose désormais `guard_reason` afin d'identifier immédiatement pourquoi le PRI ne s'exécute pas.

## Conservé
- PRI-PI 1.3.200/1.3.201.
- Comparateur PRI/PV.
- ACK PRI sur N+1.
- Protection fausse fin solaire.
- Délestage 2 trames hautes / 5 trames basses.
- Priorité des cycles machines protégés.
