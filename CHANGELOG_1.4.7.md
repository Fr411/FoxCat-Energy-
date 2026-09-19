# FoxCat Energy 1.4.7 — Réduction puissance onduleur autonome

La réduction puissance onduleur est évaluée sur chaque vraie trame 30 s,
avant le CORE EMS.

Elle n'est plus bloquée par le délestage, le boiler, la phase WAIT_ACK du CORE
ou le régime tarifaire. Les gardes restants sont : régulation globale,
activation de la réduction, mode compatible, validité des mesures/RRCR et
validation N+1 de la commande précédente.

Diagnostics ajoutés : `last_engine_run`, `engine_run_count`, `guard_reason`.

Algorithme 1.4.6 conservé : 4000 W, 10 %=400 W, réinjection => -10 %,
prélèvement + PV au plafond => +10 %, sinon maintien.
