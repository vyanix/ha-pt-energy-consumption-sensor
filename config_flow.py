"""Config flow da integração PT Energy Consumption Sensor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

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
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=28, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_CUSTO_ENERGIA_DIA, default=values[CONF_CUSTO_ENERGIA_DIA]
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=100, step="any", mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_CUSTO_ENERGIA_KWH, default=values[CONF_CUSTO_ENERGIA_KWH]
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=10, step="any", mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_CUSTO_TARIFA_SOCIAL_KWH,
                default=values[CONF_CUSTO_TARIFA_SOCIAL_KWH],
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=10, step="any", mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_CUSTO_IEC_KWH, default=values[CONF_CUSTO_IEC_KWH]
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=10, step="any", mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_CUSTO_AUDIOVISUAL, default=values[CONF_CUSTO_AUDIOVISUAL]
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=100, step=0.01, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_CUSTO_DGEG, default=values[CONF_CUSTO_DGEG]
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=100, step=0.01, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_VALOR_CONSUMO_IVA_REDUZIDO,
                default=values[CONF_VALOR_CONSUMO_IVA_REDUZIDO],
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=100000, step=1, mode=NumberSelectorMode.BOX
                )
            ),
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
