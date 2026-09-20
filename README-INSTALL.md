# FoxCat Energy - Dashboard généré automatiquement

## Fichiers GitHub

Copier dans le dépôt :

```text
custom_components/foxcat_energy/
├── __init__.py
├── button.py
├── dashboard.py
└── dashboard/
    └── dashboard.yaml
```

Le reste du composant FoxCat Energy reste inchangé.

## Fonctionnement

Au chargement de FoxCat Energy :

- si `/config/foxcat_energy/dashboard.yaml` n'existe pas, le composant le crée automatiquement ;
- s'il existe déjà, il n'est pas écrasé ;
- le bouton `Régénérer le dashboard FoxCat` permet de forcer sa régénération ;
- avant une régénération forcée, l'ancien fichier est sauvegardé en `dashboard.yaml.bak`.

## Enregistrement Lovelace

Home Assistant doit savoir que ce fichier est un dashboard YAML.
Fusionner une seule fois le contenu de `configuration.yaml.snippet` dans `/config/configuration.yaml`, puis redémarrer Home Assistant.

Ne pas modifier directement `.storage/lovelace_dashboards`.
