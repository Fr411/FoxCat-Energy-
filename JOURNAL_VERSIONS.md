# FoxCat Energy 1.5.7 — inventaire matériel informatif

- 50 marques d'onduleurs et modèles/familles usuels.
- SolarEdge SE4K ajouté explicitement et utilisé comme valeur par défaut.
- Catalogue de systèmes de mesure : Smappee, Shelly, P1/P2, compteurs Modbus,
  ESPHome, MQTT et principaux smart meters constructeurs.
- Sélections persistantes dans Home Assistant, accompagnées de deux capteurs de synthèse.
- Métadonnées strictement sans effet sur le PRI et les stratégies EMS.

# FoxCat Energy 1.5.6 — PRI souverain par trame et commande boiler utilisateur

## PRI souverain

- Chaque publication d'un capteur utile au PRI déclenche un recalcul, y compris une republication à valeur identique via `state_reported` / `last_reported` lorsque Home Assistant l'expose.
- Sources suivies : PV, consommation maison, import réseau, export réseau, réseau signé historique, métronome principal et métronome de secours.
- Suppression du throttle 30 s pour le PRI. Le métronome 30 s reste l'horloge du CORE et le fallback si aucun callback physique exploitable n'est reçu.
- Aucun mode EMS, délai boiler, hystérésis de score, ACK N+1, état de délestage ou hypothèse « PV au plafond » ne bloque plus un recalcul PRI valide.
- Le retour RRCR inconnu n'annule plus une trame : FoxCat repart du dernier niveau logique et réécrit le palier calculé.
- La commande RRCR n'attend plus un ACK avant de rendre la main. La trame suivante valide N+1 puis recalcule dans tous les cas.
- Verrou physique RRCR séparé du verrou des actions CORE/boiler.
- Le délestage ne force plus le PRI à 100 % et ne l'annule plus.
- Les modes EMS ne désarment plus le PRI.
- En « Injection facturée », la consommation maison normalisée devient la grandeur feed-forward principale. Une hausse de charge peut donc faire remonter immédiatement le palier sans attendre la propagation complète sur le compteur réseau.
- En « Compensation », le palier idéal est recalculé directement à 100 % à chaque trame.

## Mesures FoxCat normalisées

FoxCat crée et expose ses propres mesures cohérentes pour l'EMS :

- puissance de production photovoltaïque ;
- consommation réelle maison ;
- puissance réinjectée au réseau ;
- puissance prélevée au réseau ;
- balance réseau ;
- consommation maison calculée par `PV + import - export` ;
- écart entre capteur maison direct et bilan FoxCat ;
- qualité et sources des mesures ;
- compteur et source des publications ayant déclenché le PRI.

Si le capteur maison direct est indisponible, le bilan FoxCat peut prendre le relais. Si un capteur import/export séparé est indisponible, le capteur réseau signé historique peut servir de fallback.

## Boiler — demande utilisateur persistante

- Nouveau switch `Boiler • Marche utilisateur maintenue`.
- Nouveaux boutons `Démarrer le boiler` et `Arrêter le boiler`.
- Une marche demandée explicitement par l'utilisateur traverse les cycles machines protégés, les contraintes HP/HC, l'achat réseau et les stratégies énergétiques normales.
- Un arrêt automatique ordinaire est ignoré tant que la demande utilisateur est mémorisée.
- Deux interruptions restent prioritaires : sécurité thermique et délestage explicite.
- Pendant un délestage, la demande reste mémorisée et l'état indique `DÉLESTAGE EN COURS — DEMANDE MÉMORISÉE`.
- À la fin du délestage, le boiler redémarre automatiquement si la demande utilisateur est toujours active.

## Compatibilité

Aucun élément historique n'est supprimé. Les anciens réglages `pri_enabled`, `pri_score_margin` et `pri_boiler_settle_s` sont conservés pour compatibilité, mais ils ne peuvent plus bloquer le cœur PRI souverain.


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
