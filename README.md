# FoxCat Energy


## Version 1.6.0 — Sources unifiées, registre FoxCat et classement fonctionnel
FoxCat Energy utilise désormais deux sources physiques obligatoires : une puissance réseau signée et la production photovoltaïque. Le prélèvement, la réinjection et la consommation maison sont calculés par FoxCat.

Le dashboard embarqué est lié à un registre sémantique central. Les entités FoxCat natives sont résolues par `unique_id` Home Assistant; les sources physiques sont résolues depuis la configuration. Une nouvelle carte Boiler utilise uniquement ce registre.

Ordre officiel : **Sources énergétiques → Énergie → Onduleur → EMS → Energy Bus → Machines → Boiler → Tarification → Métronome → Diagnostic**. PRI reste le moteur interne de l'onduleur.

Le PRI prédictif 1.5.5, les ACK RRCR, le métronome/fallback, Energy Bus, les machines, le boiler, la tarification et la comptabilité sont conservés.

FoxCat reconstruit également lui-même l'état de cycle à partir du capteur de puissance et d'une durée théorique configurable par appareil. Une pause à 0 W pendant un lavage/séchage ne rend plus la prise disponible à l'automatisme.

États : `IDLE → START_DETECTED → PROTECTED_CYCLE → END_CONFIRMATION → FINISHED`.

Pour chaque appareil ajouté, la configuration propose : seuil de démarrage, confirmation de démarrage, durée théorique, marge maximale, seuil de fin et délai de confirmation de fin. Un ancien capteur de cycle reste accepté comme amorce utilisateur/externe, mais sa retombée à OFF ne termine plus le cycle FoxCat.

Les fonctions existantes restent conservées : EMS CORE, fallback boiler, machines, priorité utilisateur, HP/HC, dynamique, EnergyBus, EMS Onduleur, politiques Compensation/Injection facturée, comptabilité et dashboard.
