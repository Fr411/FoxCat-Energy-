# FoxCat Energy 1.6.150 — Cadencement réseau souverain et cœurs indépendants

## Objectif

Supprimer toute possibilité de trame énergétique vieillissante ou bloquée derrière une commande physique. Chaque publication réelle du capteur réseau cadence désormais simultanément EMS Core et Onduleur Core sur le même snapshot énergétique.

## Changements principaux

- Chaque publication réelle du capteur réseau principal crée immédiatement une nouvelle trame.
- Suppression de la fenêtre de 30 s comme cadence de décision : le Métronome devient uniquement un Watchdog de fraîcheur/fallback.
- EMS Core et Onduleur Core reçoivent le même numéro de trame, le même timestamp et le même snapshot.
- Les deux cœurs fonctionnent dans des tasks et verrous indépendants.
- Energy Bus transporte maintenant les décisions dans les deux sens avec ACK/NOK.
- Les messages ACK indiquent explicitement l'émetteur et le destinataire.
- Une trame Energy Bus mémorise réseau, PV, maison, import/export, Boiler, machines, mode EMS et politique réseau.
- Le PRI calcule sa décision immédiatement sur chaque publication.
- La commande RRCR est déplacée dans un worker physique séparé : une commutation ne bloque jamais la décision de la trame suivante.
- Le worker RRCR converge toujours vers la dernière cible demandée et ne constitue pas une file de vieilles consignes.
- Les appels Home Assistant du Boiler sont exécutés dans un worker séparé avec timeout.
- EMS Core ne reste donc plus bloqué sur une commande Climate.
- Le délestage demande la libération PRI via Energy Bus/worker sans bloquer EMS Core.
- Un import réseau au-dessus de l'enveloppe autorise désormais une remontée immédiate du PRI, même si le PV n'est pas formellement détecté au plafond actuel.
- Le fallback ne fabrique pas de trames artificielles : une trame fallback existe uniquement sur publication réelle du capteur de secours.
- Le Watchdog ferme explicitement toute trame restée PENDING anormalement longtemps au lieu de la laisser vieillir silencieusement.

## Diagnostics ajoutés

- Statut de la trame côté EMS Core.
- Statut de la trame côté Onduleur Core.
- Nombre de trames traitées par EMS Core.
- Nombre de trames traitées par Onduleur Core.
- Source/cible/action du dernier message Energy Bus.
- Statut et cible du worker RRCR.

## Compatibilité

Les fonctions historiques de 1.6.1-101 sont conservées. La voie legacy sans capteur Métronome explicite cadence également les deux cœurs sur la même publication réseau.

# 1.6.1-101 — Release de test : compteurs journaliers et séquences sûres

- Reset à minuit des compteurs visibles Métronome, trames et messages Energy Bus.
- Numérotation journalière propre : première trame/message du nouveau jour = 1.
- Séquence technique interne séparée pour ne jamais casser la validation PRI N+1.
- Messages Energy Bus sans ACK à minuit clôturés en TIMEOUT avant purge journalière.
- Diagnostics de la journée précédente ajoutés.
- Audit anti-régression : 275 → 278 fonctions/méthodes, 0 supprimée.

# 1.6.1

Voir `CHANGELOG_1.6.1.md`.

## 1.6.0 — Modèle énergétique unifié et registre FoxCat

- Deux sources physiques obligatoires : puissance réseau signée + production photovoltaïque.
- FoxCat dérive consommation maison, prélèvement et réinjection.
- Fallback réseau signé synchronisant à la fois la cadence et la mesure.
- Ordre fonctionnel officiel : Sources énergétiques → Énergie → Onduleur → EMS → Energy Bus → Machines → Boiler → Tarification → Métronome → Diagnostic.
- PRI reste interne; le libellé utilisateur devient Onduleur.
- Registre central des entités et dashboard 100 % résolu par rôles FoxCat.
- Nouvelle carte Boiler liée au registre.
- Capteurs Energy Bus dédiés.
- Compatibilité 1.5.x conservée jusqu'à reconfiguration des nouvelles sources.

## 1.5.5 — PRI prédictif à palier optimal

- Le métronome synchronise les données mais ne cadence plus une descente palier par palier.
- Simulation directe des 11 paliers RRCR de 0 à 100 % par pas de 10 %.
- Calcul de la charge maison par bilan `PV + import - export` et d’une puissance PV cible tenant compte de l’import cible.
- Commande directe du meilleur palier avec score réseau, pénalités hors enveloppe et hystérésis par marge de score.
- Une remontée PRI n’est utile que si le PV est bridé; si le PV est sous son plafond, augmenter la limite n’est pas considéré comme créant du solaire.
- Ajout des diagnostics : charge estimée, PV cible, import/export prévus et scores PRI actifs.
- ACK RRCR, validation N+1, métronome principal/fallback, EnergyBus et protections existantes conservés.

## 1.5.4 — Métronome réseau synchronisé

- Ajout d’un capteur métronome configurable (Smappee consommation réseau recommandé).
- Ajout d’un capteur de secours configurable avec bascule automatique si le principal devient muet.
- Détection des republications identiques via `state_reported`/`last_reported` quand Home Assistant le permet.
- Métronome interne 30 s resynchronisé par les heartbeats physiques; une seule décision PRI par battement.
- Suppression du double cadencement PRI par événements réseau parallèles lorsque le métronome est actif.
- Sécurité : si principal et secours sont périmés, les décisions PRI sont gelées au lieu d’utiliser des mesures anciennes.
- Ajout de capteurs de diagnostic métronome (statut, source, compteur, période, dernier battement, raison).

# Journal des versions FoxCat Energy

## 1.5.3 — PRI : reprise automatique si la réinjection reste inchangée
- Correction d’un blocage possible après le premier palier (par exemple 100 → 90 %) lorsque le capteur réseau republie une valeur identique sans événement `state_changed`.
- Le capteur réseau reste la source souveraine du EMS Onduleur.
- Ajout d’un filet de sécurité sur l’horloge 30 s : si aucune décision PRI n’a eu lieu depuis 25 s, une nouvelle acquisition relance le moteur.
- Les corrections restent strictement par pas de 10 % ; aucun saut direct de palier n’est introduit.
- Les protections, ACK RRCR, modes EMS, EnergyBus, cycles machines et logique existante sont conservés.

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
