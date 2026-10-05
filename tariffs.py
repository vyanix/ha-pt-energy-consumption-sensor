"""Estruturas e lógica das tarifas horárias portuguesas (ERSE).

Carrega o ficheiro ``tariffs.json`` e classifica o consumo horário do Recorder
pelos períodos horários (Vazio, Fora de Vazio, Cheio, Ponta) de acordo com a
opção tarifária (Simples, Bi-Horária, Tri-Horária) e o ciclo (Diário, Semanal).

Os horários estão definidos em hora local. A estação (verão/inverno) é
determinada automaticamente pela hora legal (DST) do momento em causa.
"""

from __future__ import annotations

import datetime
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from homeassistant.util import dt as dt_util

_DATA_FILE = Path(__file__).parent / "tariffs.json"

# Identificadores de períodos horários
PERIODO_UNICO = "unico"
PERIODO_VAZIO = "vazio"
PERIODO_FORA_VAZIO = "fora_vazio"
PERIODO_CHEIO = "cheio"
PERIODO_PONTA = "ponta"

# Identificadores de opções tarifárias
OPCAO_SIMPLES = "simples"
OPCAO_BI_HORARIA = "bi-horaria"
OPCAO_TRI_HORARIA = "tri-horaria"

# Identificadores de ciclos horários
CICLO_DIARIO = "diario"
CICLO_SEMANAL = "semanal"

# Períodos de custo que são sempre expostos como atributos (0 quando não se aplica)
PERIODOS_ATRIBUTO = [PERIODO_VAZIO, PERIODO_FORA_VAZIO, PERIODO_CHEIO, PERIODO_PONTA]


@lru_cache(maxsize=1)
def load_tariffs() -> dict[str, Any]:
    """Carrega e memoriza o conteúdo do ficheiro de tarifas."""
    with _DATA_FILE.open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def tariff_options() -> list[str]:
    """Devolve as opções tarifárias disponíveis (ex.: simples, bi-horaria)."""
    return list(load_tariffs()["opcoes_tarifarias"])


def cycle_options() -> list[str]:
    """Devolve os ciclos horários disponíveis (diario, semanal)."""
    return list(load_tariffs()["ciclos"])


def periods_for(option: str) -> list[str]:
    """Devolve os períodos horários aplicáveis a uma opção tarifária."""
    return list(load_tariffs()["opcoes_tarifarias"][option]["periodos"])


def iva_reduzido(regiao: str = "continente") -> float:
    """Multiplicador da taxa reduzida de IVA de uma região (ex.: 1.06 = 6 %)."""
    return load_tariffs()["iva"]["regioes"][regiao]["reduzido"]


def iva_normal(regiao: str = "continente") -> float:
    """Multiplicador da taxa normal de IVA de uma região (ex.: 1.23 = 23 %)."""
    return load_tariffs()["iva"]["regioes"][regiao]["normal"]


def region_options() -> list[str]:
    """Devolve as regiões de IVA disponíveis (continente, acores, madeira)."""
    return list(load_tariffs()["iva"]["regioes"])


def potencia_max_iva_reduzido() -> float:
    """Potência contratada máxima (kVA) com direito a IVA reduzido."""
    return load_tariffs()["iva"]["potencia_max_kva"]


def limite_iva_reduzido(familias_numerosas: bool = False) -> float:
    """Plafond mensal de kWh com IVA reduzido (200 geral, 300 famílias)."""
    iva = load_tariffs()["iva"]
    if familias_numerosas:
        return iva["limite_reduzido_familias_kwh"]
    return iva["limite_reduzido_kwh"]


def _to_minutes(hour_minute: str) -> int:
    """Converte 'HH:MM' em minutos desde a meia-noite."""
    hours, minutes = hour_minute.split(":")
    return int(hours) * 60 + int(minutes)


def _season(moment: datetime.datetime) -> str:
    """Devolve 'verao' ou 'inverno' com base na hora legal (DST)."""
    return "verao" if moment.dst() else "inverno"


def _day_type(moment: datetime.datetime, cycle: str) -> str:
    """Devolve o tipo de dia ('todos', 'util', 'sabado' ou 'domingo')."""
    if cycle == CICLO_DIARIO:
        return "todos"
    weekday = moment.weekday()
    if weekday < 5:
        return "util"
    if weekday == 5:
        return "sabado"
    return "domingo"


def _schedule(option: str, cycle: str, day_type: str, season: str) -> list[tuple[int, int, str]]:
    """Devolve a lista de segmentos (inicio, fim, periodo) em minutos."""
    raw = load_tariffs()["horarios"][option][cycle][day_type][season]
    return [(_to_minutes(seg["inicio"]), _to_minutes(seg["fim"]), seg["periodo"]) for seg in raw]


def _split_hour(
    start_minute: int, schedule: list[tuple[int, int, str]]
) -> dict[str, float]:
    """Reparte uma hora pelos períodos que a intersectam (fração 0..1).

    Como as estatísticas de longo prazo são horárias, a energia de cada hora é
    distribuída proporcionalmente pelo tempo que essa hora passa em cada período
    horário (ex.: uma hora que começa às 09:00 num dia com mudança às 09:15 fica
    25 % em Cheio e 75 % em Ponta).
    """
    end_minute = start_minute + 60
    fractions: dict[str, float] = {}
    for seg_start, seg_end, period in schedule:
        overlap = max(0.0, min(end_minute, seg_end) - max(start_minute, seg_start))
        if overlap > 0:
            fractions[period] = fractions.get(period, 0.0) + overlap
    return {period: minutes / 60 for period, minutes in fractions.items()}


def consumption_by_period(
    rows: list[dict[str, Any]], option: str, cycle: str
) -> dict[str, float]:
    """Agrega o consumo (kWh) de linhas horárias por período horário.

    ``rows`` são as linhas devolvidas por ``statistics_during_period`` com
    ``period="hour"`` e ``types={"change"}``; cada linha tem ``start`` (timestamp
    UTC em segundos) e ``change`` (kWh).
    """
    result: dict[str, float] = {period: 0.0 for period in periods_for(option)}

    if option == OPCAO_SIMPLES:
        result[PERIODO_UNICO] = sum(
            row["change"] for row in rows if row.get("change") is not None
        )
        return result

    for row in rows:
        change = row.get("change")
        if change is None:
            continue

        moment = dt_util.as_local(dt_util.utc_from_timestamp(row["start"]))
        day_type = _day_type(moment, cycle)
        season = _season(moment)
        schedule = _schedule(option, cycle, day_type, season)
        start_minute = moment.hour * 60 + moment.minute

        for period, fraction in _split_hour(start_minute, schedule).items():
            if period in result:
                result[period] += change * fraction

    return result
