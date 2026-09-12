# FoxCat Energy 1.1.0 — 12 septembre 2026

## EMS Machines
- Deux plages ON/OFF configurables par machine dans l'onglet Machines.
- Valeurs par défaut conservées : 21:30–07:00 et 10:30–17:00.
- Lave-linge, sèche-linge et lave-vaisselle peuvent avoir des horaires différents.
- Un cycle déjà démarré reste prioritaire et n'est jamais interrompu par la fin d'une plage horaire.

## PRI zéro injection
- La décision PRI ne dépend plus de la consommation maison.
- La réinjection réseau est l'erreur principale à supprimer.
- Si la réinjection dépasse le seuil acceptable, descente d'une seule marche de 10 %.
- Si le prélèvement dépasse le seuil acceptable, remontée prudente d'une seule marche de 10 %.
- La réinjection est traitée avant le prélèvement lors d'une mesure transitoire incohérente.
- Les capteurs réseau import/export déclenchent directement la régulation PRI.
- Suppression de l'attente initiale de 30 s avant décision afin de ne plus agir sur une mesure T0 devenue ancienne.
- Le rollback après remontée reste conservé si la réinjection redevient excessive.

## Noms d'entités
- Harmonisation des noms visibles en français.
- Les puissances sont explicitement nommées « Puissance ... ».
- La production, la consommation, le prélèvement et la réinjection sont distingués clairement.
- Les unique_id sont conservés afin d'éviter de casser les entités déjà enregistrées dans Home Assistant.

## Statut
À TESTER sur installation réelle avant validation production.
