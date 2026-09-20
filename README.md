# FoxCat Energy 1.5.7

## Matériel installé — métadonnées uniquement

FoxCat peut maintenant mémoriser et afficher le matériel de l'installation sans
modifier son comportement énergétique. Quatre sélecteurs Home Assistant permettent
de choisir la marque et le modèle/famille de l'onduleur ainsi que le système et le
modèle/interface de mesure principal. Le catalogue contient 50 fabricants
d'onduleurs ; SolarEdge / SE4K est le défaut de cette installation. Les solutions
de mesure comprennent notamment Smappee Infinity/Genius, Shelly, P1/P2, HomeWizard,
Tibber, Eastron, Carlo Gavazzi, ESPHome, Modbus et MQTT.

Aucune de ces sélections n'est utilisée dans le calcul PRI ou les autres décisions
EMS. Le catalogue est descriptif et extensible.

# FoxCat Energy


## Version 1.5.6 — PRI souverain par trame

Le PRI recalcule désormais son palier idéal à **chaque publication de mesure**, y compris une valeur identique lorsque Home Assistant expose `state_reported`. Aucun mode EMS, délai boiler, hystérésis, ACK ou état de délestage ne bloque une trame PRI valide. La consommation maison FoxCat pilote directement la remontée/descente et la trame suivante corrige toute estimation imparfaite.

FoxCat expose maintenant une couche de mesures normalisées (PV, maison, import, export, balance, maison calculée, qualité et sources) et ajoute une **demande boiler utilisateur persistante** avec boutons Marche/Arrêt. Cette demande n'est interrompue que par la sécurité thermique ou un délestage explicite, puis elle reprend automatiquement après délestage.

## Version 1.5.5 — PRI prédictif à palier optimal
Le métronome Smappee garantit désormais une trame réseau fraîche tandis que le moteur PRI simule les paliers RRCR 0–100 % et commande directement le meilleur niveau, sans descendre artificiellement d'un palier toutes les 30 secondes.

Le calcul s'appuie sur le bilan instantané `PV + import - export`, la cible de léger prélèvement et les limites d'import/réinjection configurées. Les ACK RRCR/N+1, le fallback métronome et les protections existantes sont conservés.

FoxCat reconstruit également lui-même l'état de cycle à partir du capteur de puissance et d'une durée théorique configurable par appareil. Une pause à 0 W pendant un lavage/séchage ne rend plus la prise disponible à l'automatisme.

États : `IDLE → START_DETECTED → PROTECTED_CYCLE → END_CONFIRMATION → FINISHED`.

Pour chaque appareil ajouté, la configuration propose : seuil de démarrage, confirmation de démarrage, durée théorique, marge maximale, seuil de fin et délai de confirmation de fin. Un ancien capteur de cycle reste accepté comme amorce utilisateur/externe, mais sa retombée à OFF ne termine plus le cycle FoxCat.

Les fonctions existantes restent conservées : EMS CORE, fallback boiler, machines, priorité utilisateur, HP/HC, dynamique, EnergyBus, EMS Onduleur, politiques Compensation/Injection facturée, comptabilité et dashboard.
