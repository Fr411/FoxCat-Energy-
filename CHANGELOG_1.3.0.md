# FoxCat Energy 1.3.0

## Machines ON/OFF extensibles

- Phase 1 de l’architecture appareils extensibles.
- Ajout / édition / suppression de machines depuis les options de l’intégration.
- Champs : identifiant stable, nom, prise, cycle protégé optionnel, capteur de puissance optionnel, gestion automatique, deux plages horaires.
- Migration transparente des trois machines historiques.
- Le mode Manuel laisse les prises machines entièrement à l’utilisateur.

## Boiler et cycles protégés

- Suppression du blocage absolu boiler lorsqu’une machine protégée est active.
- Autorisation basée sur le surplus solaire réellement mesuré au compteur.
- Si le boiler est déjà ON, sa puissance mesurée est réintégrée pour reconstruire le surplus disponible avant sa propre charge.
- Démarrage pendant un cycle protégé uniquement après validation stable sur deux trames.
- La sécurité thermique et le délestage du boiler restent souverains ; la machine protégée n’est jamais interrompue par ce délestage.
