# Journal des versions FoxCat Energy

## 1.5.2 — Protection native des cycles machines
- Ajout du `MachineCycleManager`.
- Détection de démarrage par puissance confirmée dans le temps.
- Durée théorique configurable individuellement par appareil.
- Les pauses à 0 W n'interrompent plus la protection.
- Fin confirmée seulement après durée théorique + faible puissance continue.
- Timeout de sécurité configurable.
- Le capteur cycle existant peut amorcer un cycle utilisateur, mais ne peut plus le terminer prématurément.
- Priorité utilisateur, tarif, délestage, EMS CORE, EnergyBus, EMS Onduleur et dashboard préservés.

## 1.5.1 — Stabilisation
- Source réseau souveraine unique pour EMS Onduleur.
- Correction du capteur réseau legacy et diagnostics de trame.

## 1.5.0 — Double cœur
- EMS CORE ↔ EnergyBus ↔ EMS Onduleur.
- Compensation / Injection facturée.
- Comparateur PV/plafond et comptabilité HP/HC par appareil.
