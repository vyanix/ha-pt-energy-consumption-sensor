"""Sensores da integração PT Energy Consumption Sensor.

A integração expõe duas entidades por config entry:

* ``sensor.custo_total_de_energia``      -> custo total estimado do ciclo (EUR)
* ``sensor.consumo_do_ciclo_de_faturacao`` -> energia consumida no ciclo (kWh)

Ambas partilham um ``DataUpdateCoordinator`` que lê as estatísticas de longo
prazo do Recorder (via API pública) e recalcula os valores a cada 30 minutos.
"""

from __future__ import annotations

import calendar
import datetime
import logging
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CUSTO_AUDIOVISUAL,
    CONF_CUSTO_DGEG,
    CONF_CUSTO_ENERGIA_DIA,
    CONF_CUSTO_ENERGIA_KWH,
    CONF_CUSTO_IEC_KWH,
    CONF_CUSTO_TARIFA_SOCIAL_KWH,
    CONF_DIA_INICIO_FATURACAO,
    CONF_STATISTIC_ID,
    CONF_VALOR_CONSUMO_IVA_REDUZIDO,
    DEFAULTS,
    DOMAIN,
    IVA_NORMAL,
    IVA_REDUZIDO,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(minutes=30)


def _safe_replace_day(moment: datetime.datetime, day: int) -> datetime.datetime:
    """Substitui o dia do mês com clamp para meses mais curtos (ex.: dia 31)."""
    last_day = calendar.monthrange(moment.year, moment.month)[1]
    return moment.replace(
        day=min(day, last_day), hour=0, minute=0, second=0, microsecond=0
    )


def billing_cycle_start(now: datetime.datetime, start_day: int) -> datetime.datetime:
    """Devolve o início do ciclo de faturação que contém ``now``."""
    if now.day >= start_day:
        return _safe_replace_day(now, start_day)

    first_of_this_month = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    last_month_last_day = first_of_this_month - datetime.timedelta(days=1)
    return _safe_replace_day(last_month_last_day, start_day)


class PTEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Consulta as estatísticas do Recorder uma vez por ciclo de atualização."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry

    def get_config(self, key: str, default: Any) -> Any:
        """Prioriza as opções (OptionsFlow) sobre os dados iniciais."""
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # A leitura das estatísticas tem de correr no executor de base de
            # dados do Recorder (não no executor genérico), caso contrário o
            # Home Assistant emite um aviso de acesso à BD sem o DB executor.
            return await get_instance(self.hass).async_add_executor_job(
                self._calculate
            )
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Erro ao calcular o custo energético: {err}") from err

    def _calculate(self) -> dict[str, Any]:
        """Consulta as estatísticas do Recorder (em executor) e faz os cálculos."""
        now = dt_util.now()
        start_date = billing_cycle_start(
            now,
            int(
                self.get_config(
                    CONF_DIA_INICIO_FATURACAO, DEFAULTS[CONF_DIA_INICIO_FATURACAO]
                )
            ),
        )

        statistic_id: str = self.get_config(
            CONF_STATISTIC_ID, DEFAULTS[CONF_STATISTIC_ID]
        )
        total_kwh = self._query_total_kwh(statistic_id, start_date, now)

        custo_energia_dia = float(
            self.get_config(CONF_CUSTO_ENERGIA_DIA, DEFAULTS[CONF_CUSTO_ENERGIA_DIA])
        )
        custo_energia_kwh = float(
            self.get_config(CONF_CUSTO_ENERGIA_KWH, DEFAULTS[CONF_CUSTO_ENERGIA_KWH])
        )
        custo_tarifa_social_kwh = float(
            self.get_config(
                CONF_CUSTO_TARIFA_SOCIAL_KWH, DEFAULTS[CONF_CUSTO_TARIFA_SOCIAL_KWH]
            )
        )
        custo_iec_kwh = float(
            self.get_config(CONF_CUSTO_IEC_KWH, DEFAULTS[CONF_CUSTO_IEC_KWH])
        )
        custo_audiovisual = float(
            self.get_config(CONF_CUSTO_AUDIOVISUAL, DEFAULTS[CONF_CUSTO_AUDIOVISUAL])
        )
        custo_dgeg = float(
            self.get_config(CONF_CUSTO_DGEG, DEFAULTS[CONF_CUSTO_DGEG])
        )
        limite_iva_reduzido = float(
            self.get_config(
                CONF_VALOR_CONSUMO_IVA_REDUZIDO,
                DEFAULTS[CONF_VALOR_CONSUMO_IVA_REDUZIDO],
            )
        )

        if total_kwh > limite_iva_reduzido:
            kwh_iva_reduzido = limite_iva_reduzido
            kwh_iva_normal = total_kwh - limite_iva_reduzido
        else:
            kwh_iva_reduzido = total_kwh
            kwh_iva_normal = 0.0

        dias = (now.date() - start_date.date()).days + 1

        subtotal_iva_reduzido = (kwh_iva_reduzido * custo_energia_kwh) * IVA_REDUZIDO
        subtotal_iva_normal = (kwh_iva_normal * custo_energia_kwh) * IVA_NORMAL
        subtotal_energia_dia = (custo_energia_dia * dias) * IVA_NORMAL
        subtotal_tarifa_social = (
            (kwh_iva_reduzido * custo_tarifa_social_kwh) * IVA_REDUZIDO
            + (kwh_iva_normal * custo_tarifa_social_kwh) * IVA_NORMAL
        )
        subtotal_iec = (total_kwh * custo_iec_kwh) * IVA_NORMAL
        subtotal_audiovisual = custo_audiovisual * IVA_REDUZIDO
        subtotal_dgeg = custo_dgeg * IVA_NORMAL

        total = (
            subtotal_energia_dia
            + subtotal_iva_reduzido
            + subtotal_iva_normal
            + subtotal_tarifa_social
            + subtotal_iec
            + subtotal_audiovisual
            + subtotal_dgeg
        )

        return {
            "total_cost": round(total, 2),
            "total_kwh": round(total_kwh, 2),
            "dias": dias,
            "start_date": start_date,
            "end_date": now,
            "breakdown": {
                "energia_dia": round(subtotal_energia_dia, 2),
                "energia_iva_reduzido": round(subtotal_iva_reduzido, 2),
                "energia_iva_normal": round(subtotal_iva_normal, 2),
                "tarifa_social": round(subtotal_tarifa_social, 2),
                "iec": round(subtotal_iec, 2),
                "audiovisual": round(subtotal_audiovisual, 2),
                "dgeg": round(subtotal_dgeg, 2),
                "kwh_iva_reduzido": round(kwh_iva_reduzido, 2),
                "kwh_iva_normal": round(kwh_iva_normal, 2),
            },
        }

    def _query_total_kwh(
        self,
        statistic_id: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> float:
        """Devolve o consumo (kWh) desde ``start_date`` até ``end_date``.

        Usa a API pública do Recorder em vez de aceder diretamente ao SQLite.
        Com ``period="hour"`` e ``types={"change"}``, cada linha traz a variação
        do ``sum`` nessa hora e a primeira hora é medida a partir do ``sum``
        imediatamente anterior ao início do ciclo, pelo que a soma dos ``change``
        corresponde ao consumo exato desde o início do ciclo.
        """
        stats = statistics_during_period(
            self.hass,
            dt_util.as_utc(start_date),
            dt_util.as_utc(end_date),
            {statistic_id},
            "hour",
            {"energy": "kWh"},
            {"change"},
        )

        rows = stats.get(statistic_id, [])
        return sum(
            row["change"] for row in rows if row.get("change") is not None
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura os sensores de energia PT através de uma Config Entry."""
    coordinator = PTEnergyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            PTEnergyCostSensor(coordinator, entry),
            PTEnergyConsumptionSensor(coordinator, entry),
        ]
    )


class PTEnergyBaseSensor(CoordinatorEntity[PTEnergyCoordinator], SensorEntity):
    """Base comum aos sensores da integração."""

    def __init__(
        self, coordinator: PTEnergyCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Vyanix Power Monitor",
            manufacturer="Vyanix",
            model="Energy Meter v1",
            sw_version="1.2.0",
        )


class PTEnergyCostSensor(PTEnergyBaseSensor):
    """Custo total estimado do ciclo de faturação (EUR)."""

    _attr_name = "Custo Total de Energia"
    _attr_native_unit_of_measurement = "EUR"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash-fast"
    _attr_suggested_display_precision = 2

    def __init__(
        self, coordinator: PTEnergyCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"vyanix_energy_total_cost_{entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("total_cost")

    @property
    def last_reset(self) -> datetime.datetime:
        return self.coordinator.data["start_date"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        start_date: datetime.datetime = data["start_date"]
        end_date: datetime.datetime = data["end_date"]
        return {
            "total_kwh": data["total_kwh"],
            "dias_ciclo": data["dias"],
            "inicio_ciclo": start_date.strftime("%Y-%m-%d"),
            "fim_ciclo": end_date.strftime("%Y-%m-%d"),
            "detalhe_custos": data["breakdown"],
        }


class PTEnergyConsumptionSensor(PTEnergyBaseSensor):
    """Energia consumida desde o início do ciclo de faturação (kWh)."""

    _attr_name = "Consumo do Ciclo de Faturação"
    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:lightning-bolt"
    _attr_suggested_display_precision = 2

    def __init__(
        self, coordinator: PTEnergyCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"vyanix_energy_cycle_consumption_{entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("total_kwh")

    @property
    def last_reset(self) -> datetime.datetime:
        return self.coordinator.data["start_date"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            "inicio_ciclo": data["start_date"].strftime("%Y-%m-%d"),
            "fim_ciclo": data["end_date"].strftime("%Y-%m-%d"),
            "dias_ciclo": data["dias"],
        }
