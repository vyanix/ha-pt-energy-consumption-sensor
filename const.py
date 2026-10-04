"""Constantes da integração PT Energy Consumption Sensor."""

DOMAIN = "pt_energy_consumption_sensor"

# --- Chaves de configuração -------------------------------------------------
# Mantidas em camelCase por compatibilidade com instalações existentes.
CONF_STATISTIC_ID = "statistic_id"
CONF_DIA_INICIO_FATURACAO = "diaInicioFaturacao"
CONF_CUSTO_ENERGIA_DIA = "custoEnergiaDia"
CONF_CUSTO_ENERGIA_KWH = "custoEnergiaKwh"
CONF_CUSTO_TARIFA_SOCIAL_KWH = "custoTarifaSocialKwh"
CONF_CUSTO_IEC_KWH = "custoIECKwh"
CONF_CUSTO_AUDIOVISUAL = "custoAudiovisual"
CONF_CUSTO_DGEG = "custoDGEG"
CONF_VALOR_CONSUMO_IVA_REDUZIDO = "valorConsumoIVAReduzido"

# --- Valores por defeito ----------------------------------------------------
# O sensor de consumo é escolhido pelo utilizador na configuração (sem default),
# para não impor nenhum dispositivo específico nem expor identificadores pessoais.
DEFAULT_STATISTIC_ID = ""
DEFAULT_DIA_INICIO_FATURACAO = 11
DEFAULT_CUSTO_ENERGIA_DIA = 0.4624
DEFAULT_CUSTO_ENERGIA_KWH = 0.1337
DEFAULT_CUSTO_TARIFA_SOCIAL_KWH = 0.0017
DEFAULT_CUSTO_IEC_KWH = 0.0010
DEFAULT_CUSTO_AUDIOVISUAL = 2.85
DEFAULT_CUSTO_DGEG = 0.07
DEFAULT_VALOR_CONSUMO_IVA_REDUZIDO = 200

DEFAULTS: dict[str, object] = {
    CONF_STATISTIC_ID: DEFAULT_STATISTIC_ID,
    CONF_DIA_INICIO_FATURACAO: DEFAULT_DIA_INICIO_FATURACAO,
    CONF_CUSTO_ENERGIA_DIA: DEFAULT_CUSTO_ENERGIA_DIA,
    CONF_CUSTO_ENERGIA_KWH: DEFAULT_CUSTO_ENERGIA_KWH,
    CONF_CUSTO_TARIFA_SOCIAL_KWH: DEFAULT_CUSTO_TARIFA_SOCIAL_KWH,
    CONF_CUSTO_IEC_KWH: DEFAULT_CUSTO_IEC_KWH,
    CONF_CUSTO_AUDIOVISUAL: DEFAULT_CUSTO_AUDIOVISUAL,
    CONF_CUSTO_DGEG: DEFAULT_CUSTO_DGEG,
    CONF_VALOR_CONSUMO_IVA_REDUZIDO: DEFAULT_VALOR_CONSUMO_IVA_REDUZIDO,
}

# --- Taxas de IVA (multiplicadores) ----------------------------------------
IVA_REDUZIDO = 1.06  # 6 %
IVA_NORMAL = 1.23  # 23 %
