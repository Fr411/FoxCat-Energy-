# FoxCat Energy 1.3.1

## Délestage haute consommation

- Ajout d’un détecteur de haute consommation basé sur la puissance réelle de la maison.
- Fonction désactivée par défaut.
- Seuil de déclenchement, seuil de réarmement, temps de confirmation et temporisation de retour configurables.
- Lors d’un délestage : chauffe-eau arrêté, PRI libéré à 100 %, charges machines marquées délestables coupées si aucun cycle protégé n’est actif.
- Un cycle protégé déjà démarré n’est jamais interrompu.
- Hystérésis et temporisations évitent les oscillations pendant les pointes de cuisine/préparation des repas.
- Le mode Manuel conserve la main et inhibe ce délestage automatique.
- Ajout du capteur binaire `Délestage haute consommation actif` et du capteur `Statut délestage haute consommation`.

## Appareils extensibles

- Chaque machine extensible possède désormais l’option `Charge délestable en haute consommation`.
- Valeur par défaut : activée, sans interruption d’un cycle protégé actif.
