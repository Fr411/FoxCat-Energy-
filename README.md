# FoxCat Energy


## Version 1.5.5 — PRI prédictif à palier optimal
Le métronome Smappee garantit désormais une trame réseau fraîche tandis que le moteur PRI simule les paliers RRCR 0–100 % et commande directement le meilleur niveau, sans descendre artificiellement d'un palier toutes les 30 secondes.

Le calcul s'appuie sur le bilan instantané `PV + import - export`, la cible de léger prélèvement et les limites d'import/réinjection configurées. Les ACK RRCR/N+1, le fallback métronome et les protections existantes sont conservés.

FoxCat reconstruit également lui-même l'état de cycle à partir du capteur de puissance et d'une durée théorique configurable par appareil. Une pause à 0 W pendant un lavage/séchage ne rend plus la prise disponible à l'automatisme.

États : `IDLE → START_DETECTED → PROTECTED_CYCLE → END_CONFIRMATION → FINISHED`.

Pour chaque appareil ajouté, la configuration propose : seuil de démarrage, confirmation de démarrage, durée théorique, marge maximale, seuil de fin et délai de confirmation de fin. Un ancien capteur de cycle reste accepté comme amorce utilisateur/externe, mais sa retombée à OFF ne termine plus le cycle FoxCat.

Les fonctions existantes restent conservées : EMS CORE, fallback boiler, machines, priorité utilisateur, HP/HC, dynamique, EnergyBus, EMS Onduleur, politiques Compensation/Injection facturée, comptabilité et dashboard.
