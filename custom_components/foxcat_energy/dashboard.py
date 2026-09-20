from __future__ import annotations

from pathlib import Path
import shutil

from homeassistant.core import HomeAssistant

DASHBOARD_FOLDER = "foxcat_energy"
DASHBOARD_FILENAME = "dashboard.yaml"


def _source_path() -> Path:
    return Path(__file__).parent / "dashboard" / DASHBOARD_FILENAME


def _target_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DASHBOARD_FOLDER, DASHBOARD_FILENAME))


def _write_dashboard(source: Path, target: Path, make_backup: bool) -> str:
    if not source.exists():
        raise FileNotFoundError(f"Dashboard FoxCat introuvable: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)

    if make_backup and target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)

    content = source.read_text(encoding="utf-8")

    # Ecriture atomique : on ne laisse jamais un dashboard partiellement écrit.
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(target)

    return str(target)


async def async_ensure_dashboard(hass: HomeAssistant) -> tuple[bool, str]:
    """Crée le dashboard officiel s'il n'existe pas encore.

    Cette fonction ne remplace jamais un dashboard déjà présent afin de
    préserver les personnalisations locales de l'utilisateur.
    """
    source = _source_path()
    target = _target_path(hass)

    if target.exists():
        return False, str(target)

    path = await hass.async_add_executor_job(
        _write_dashboard,
        source,
        target,
        False,
    )
    return True, path


async def async_regenerate_dashboard(hass: HomeAssistant) -> str:
    """Régénère le dashboard depuis le modèle embarqué.

    Si un dashboard existe déjà, une sauvegarde dashboard.yaml.bak est créée
    avant son remplacement.
    """
    return await hass.async_add_executor_job(
        _write_dashboard,
        _source_path(),
        _target_path(hass),
        True,
    )
