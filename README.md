# FoxCat Energy


## Version 1.5.3 — PRI robuste sur réinjection stable
FoxCat reconstruit désormais lui-même l'état de cycle à partir du capteur de puissance et d'une durée théorique configurable par appareil. Une pause à 0 W pendant un lavage/séchage ne rend plus la prise disponible à l'automatisme.

États : `IDLE → START_DETECTED → PROTECTED_CYCLE → END_CONFIRMATION → FINISHED`.

Pour chaque appareil ajouté, la configuration propose : seuil de démarrage, confirmation de démarrage, durée théorique, marge maximale, seuil de fin et délai de confirmation de fin. Un ancien capteur de cycle reste accepté comme amorce utilisateur/externe, mais sa retombée à OFF ne termine plus le cycle FoxCat.

Les fonctions existantes restent conservées : EMS CORE, fallback boiler, machines, priorité utilisateur, HP/HC, dynamique, EnergyBus, EMS Onduleur, politiques Compensation/Injection facturée, comptabilité et dashboard.
