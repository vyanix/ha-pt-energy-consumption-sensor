"""Config flow da integração PT Energy Consumption Sensor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from . import tariffs
from .const import (
    CONF_CICLO_HORARIO,
    CONF_CUSTO_AUDIOVISUAL,
    CONF_CUSTO_CHEIO_KWH,
    CONF_CUSTO_DGEG,
    CONF_CUSTO_ENERGIA_DIA,
    CONF_CUSTO_ENERGIA_KWH,
    CONF_CUSTO_FORA_VAZIO_KWH,
    CONF_CUSTO_IEC_KWH,
    CONF_CUSTO_PONTA_KWH,
    CONF_CUSTO_TARIFA_SOCIAL_KWH,
    CONF_CUSTO_VAZIO_KWH,
    CONF_DIA_INICIO_FATURACAO,
    CONF_FAMILIAS_NUMEROSAS,
    CONF_OPCAO_TARIFARIA,
    CONF_POTENCIA_CONTRATADA,
    CONF_REGIAO,
    CONF_STATISTIC_ID,
    DEFAULTS,
    DOMAIN,
)


def _get_defaults(entry: ConfigEntry | None = None) -> dict[str, Any]:
    """Combina os valores por defeito com os guardados na entrada."""
    values = dict(DEFAULTS)
    if entry is not None:
        for key in values:
            if key in entry.options:
                values[key] = entry.options[key]
            elif key in entry.data:
                values[key] = entry.data[key]
    return values


def _select_options(group: str) -> list[SelectOptionDict]:
    """Constrói a lista de opções de um grupo (opções tarifárias ou ciclos)."""
    return [
        SelectOptionDict(value=value, label=info["nome"])
        for value, info in tariffs.load_tariffs()[group].items()
    ]


def _region_options() -> list[SelectOptionDict]:
    """Constrói a lista de regiões de IVA (Continente, Açores, Madeira)."""
    return [
        SelectOptionDict(value=value, label=info["nome"])
        for value, info in tariffs.load_tariffs()["iva"]["regioes"].items()
    ]


def _number(
    minimum: float,
    maximum: float,
    step: float | str,
    unit: str | None = None,
) -> NumberSelector:
    """Atalho para um NumberSelector em modo caixa, com unidade opcional.

    A chave ``unit_of_measurement`` só é incluída quando existe unidade, porque
    o Home Assistant rejeita um valor ``None`` nessa chave (origina erro 400).
    """
    config: dict[str, Any] = {
        "min": minimum,
        "max": maximum,
        "step": step,
        "mode": NumberSelectorMode.BOX,
    }
    if unit is not None:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def _build_schema(values: dict[str, Any]) -> vol.Schema:
    """Constrói o schema comum aos passos de configuração e de opções."""
    return vol.Schema(
        {
            # Sem default: o utilizador tem de escolher explicitamente o sensor
            # de energia acumulada (kWh) que mede o consumo geral da instalação.
            vol.Required(
                CONF_STATISTIC_ID,
                default=values.get(CONF_STATISTIC_ID) or vol.UNDEFINED,
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_DIA_INICIO_FATURACAO, default=values[CONF_DIA_INICIO_FATURACAO]
            ): _number(1, 28, 1),
            vol.Required(
                CONF_OPCAO_TARIFARIA, default=values[CONF_OPCAO_TARIFARIA]
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_select_options("opcoes_tarifarias"),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_CICLO_HORARIO, default=values[CONF_CICLO_HORARIO]
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_select_options("ciclos"),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_POTENCIA_CONTRATADA, default=values[CONF_POTENCIA_CONTRATADA]
            ): _number(1.15, 41.4, "any", "kVA"),
            vol.Required(
                CONF_FAMILIAS_NUMEROSAS, default=values[CONF_FAMILIAS_NUMEROSAS]
            ): BooleanSelector(),
            vol.Required(
                CONF_REGIAO, default=values[CONF_REGIAO]
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_region_options(),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            # Preço para a tarifa simples (preço único, 24h/dia).
            vol.Required(
                CONF_CUSTO_ENERGIA_KWH, default=values[CONF_CUSTO_ENERGIA_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            # Preços por período horário (usados nas tarifas bi/tri-horárias).
            vol.Required(
                CONF_CUSTO_VAZIO_KWH, default=values[CONF_CUSTO_VAZIO_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_FORA_VAZIO_KWH, default=values[CONF_CUSTO_FORA_VAZIO_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_CHEIO_KWH, default=values[CONF_CUSTO_CHEIO_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_PONTA_KWH, default=values[CONF_CUSTO_PONTA_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_ENERGIA_DIA, default=values[CONF_CUSTO_ENERGIA_DIA]
            ): _number(0, 100, "any", "EUR/dia"),
            vol.Required(
                CONF_CUSTO_TARIFA_SOCIAL_KWH,
                default=values[CONF_CUSTO_TARIFA_SOCIAL_KWH],
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_IEC_KWH, default=values[CONF_CUSTO_IEC_KWH]
            ): _number(0, 10, "any", "EUR/kWh"),
            vol.Required(
                CONF_CUSTO_AUDIOVISUAL, default=values[CONF_CUSTO_AUDIOVISUAL]
            ): _number(0, 100, 0.01, "EUR"),
            vol.Required(
                CONF_CUSTO_DGEG, default=values[CONF_CUSTO_DGEG]
            ): _number(0, 100, 0.01, "EUR"),
        }
    )


class PTEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow para PT Energy Consumption Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Passo inicial de configuração quando se adiciona a integração."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_STATISTIC_ID):
                errors["base"] = "missing_sensor"
            else:
                return self.async_create_entry(
                    title="PT Energy Consumption", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=_build_schema(_get_defaults()), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "PTEnergyOptionsFlowHandler":
        """Define o fluxo para gerir as opções após a integração instalada."""
        return PTEnergyOptionsFlowHandler()


class PTEnergyOptionsFlowHandler(config_entries.OptionsFlow):
    """Gere as opções/atualizações de parâmetros da integração."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Gerir o painel de opções que abre ao clicar na roda dentada."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_STATISTIC_ID):
                errors["base"] = "missing_sensor"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(_get_defaults(self.config_entry)),
            errors=errors,
        )
