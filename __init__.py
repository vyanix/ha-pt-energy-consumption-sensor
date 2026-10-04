"""Integração PT Energy Consumption Sensor.

Estimativa do custo da fatura de energia elétrica em Portugal e do consumo
do ciclo de faturação, a partir de um sensor de energia acumulada (kWh).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurar a integração a partir de uma entrada de configuração (UI)."""
    hass.data.setdefault(DOMAIN, {})

    # Guarda a entrada no dicionário global da integração para acesso nas
    # entidades e regista o listener para recarregar quando as opções mudam.
    hass.data[DOMAIN][entry.entry_id] = entry
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remover uma entrada de configuração."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recarrega a integração quando as opções mudam na roda dentada."""
    await hass.config_entries.async_reload(entry.entry_id)
