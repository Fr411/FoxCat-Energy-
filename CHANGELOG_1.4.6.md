# FoxCat Energy 1.4.6 — Réduction puissance onduleur

Moteur reconstruit autour de sa fonction fondamentale.

- Onduleur : 4000 W.
- Palier : 10 % = 400 W.
- Réinjection > seuil : -10 %.
- Prélèvement > seuil + PV proche du plafond autorisé : +10 %.
- Prélèvement mais PV sous le plafond : maintien, maximum solaire instantané atteint.
- Zone neutre : maintien.
- Une décision par trame 30 s, puis validation RRCR à la trame suivante.

Le nom utilisateur devient « Réduction puissance onduleur ».
Les identifiants internes `pri_*` restent inchangés pour préserver la compatibilité.
