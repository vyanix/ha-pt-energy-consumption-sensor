# PT Energy Consumption Sensor

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.3%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Integração personalizada para **Home Assistant** que estima o **custo da fatura de
energia elétrica em Portugal** e o **consumo do ciclo de faturação**, a partir de um
sensor de energia acumulada (kWh) — tipicamente um **Shelly EM / Shelly 3EM**.

> ⚠️ **Requisito obrigatório**
> Esta integração **não mede consumo por si própria**. Ela depende de um sensor
> existente no Home Assistant que:
>
> 1. Meça **energia acumulada em kWh** (`device_class: energy`, `state_class: total`
>    ou `total_increasing`); e
> 2. Represente o **consumo geral** da instalação (não apenas um equipamento).
>
> O caso típico é um **Shelly EM / Shelly 3EM** com um canal a medir o quadro geral.
> **Sem este sensor a integração não consegue calcular nada** (devolverá sempre 0).
> Pode ser indicado qualquer sensor de energia compatível, não tem de ser Shelly.

---

## ✨ O que a integração cria

Por cada entrada de configuração são criadas **duas entidades**, associadas a um
dispositivo virtual *Vyanix Power Monitor*:

| Entidade | Unidade | Descrição |
|---|---|---|
| `sensor.custo_total_de_energia` | EUR | Custo total estimado do ciclo de faturação (energia + taxas + IVA) |
| `sensor.consumo_do_ciclo_de_faturacao` | kWh | Energia consumida desde o início do ciclo de faturação |

O sensor de custo expõe ainda os atributos:
`total_kwh`, `dias_ciclo`, `inicio_ciclo`, `fim_ciclo` e `detalhe_custos`
(com o detalhe de cada rubrica: energia, tarifa social, IEC, audiovisual, DGEG e IVA).

O sensor de consumo expõe `inicio_ciclo`, `fim_ciclo` e `dias_ciclo`, e usa
`last_reset` para que as estatísticas de longo prazo reiniciem a cada ciclo.

---

## 🧮 Como o custo é calculado

O ciclo de faturação começa no **dia configurado** (ex.: dia 11). Os cálculos aplicam:

- **Energia (kWh)** — até ao limite definido leva **IVA reduzido (6 %)**; acima desse
  limite leva **IVA normal (23 %)**.
- **Custo de potência/dia** — valor diário × número de dias do ciclo × IVA normal.
- **Tarifa social** — por kWh, com IVA reduzido/normal conforme o escalão.
- **IEC** — imposto especial de consumo por kWh × IVA normal.
- **Taxa audiovisual** — valor fixo × IVA reduzido.
- **Taxa DGEG** — valor fixo × IVA normal.

> Os valores por defeito são apenas um ponto de partida. Ajuste-os aos da sua
> comercializadora e ao seu contrato.

---

## 📦 Instalação

### Via HACS

1. HACS → Integrações → menu (⋮) → **Repositórios personalizados**.
2. Adicione `https://github.com/vyanix/ha-pt-energy-consumption-sensor` como
   categoria **Integration**.
3. Instale **PT Energy Consumption Sensor** e reinicie o Home Assistant.

### Manual

Copie a pasta `pt_energy_consumption_sensor` para
`/config/custom_components/` e reinicie o Home Assistant.

---

## ⚙️ Configuração

1. **Definições → Dispositivos e Serviços → Adicionar integração → PT Energy Consumption Sensor**.
2. Preencha os parâmetros:

| Campo | Descrição | Exemplo |
|---|---|---|
| Sensor de consumo geral (Shelly) | Entidade de energia acumulada (kWh) do consumo geral | `sensor.shellyem_..._energy` |
| Dia do início do ciclo de faturação | Dia do mês em que começa a faturação | `11` |
| Custo de energia por dia (€) | Termo fixo diário de potência | `0.4624` |
| Custo de energia por kWh (€) | Preço da energia por kWh | `0.1337` |
| Tarifa social por kWh (€) | Contribuição da tarifa social | `0.0017` |
| Imposto IEC por kWh (€) | Imposto especial de consumo | `0.0010` |
| Taxa audiovisual (€) | Taxa de contribuição audiovisual | `2.85` |
| Taxa DGEG (€) | Taxa da entidade reguladora | `0.07` |
| Limite de consumo com IVA reduzido (kWh) | Limite do escalão de IVA reduzido | `200` |

3. Pode alterar tudo mais tarde através da **roda dentada (Opções)** da integração.
   A integração recarrega automaticamente após guardar.

---

## 🔍 Resolução de problemas

- **Custo/consumo sempre a 0** — verifique se o sensor indicado existe, mede em
  **kWh** e tem **estatísticas de longo prazo** ativas (a integração lê as
  estatísticas do Recorder).
- **Valores estranhos** — confirme as tarifas e o dia de início do ciclo.
- **Ícone/logo em falta** — o ícone local (`brand/`) requer **Home Assistant 2026.3
  ou superior**. Em versões anteriores a integração funciona, mas pode mostrar o
  placeholder "icon not available". Alternativa: contribuir as imagens para o
  repositório [home-assistant/brands](https://github.com/home-assistant/brands).

---

## 🛠️ Notas técnicas

- A leitura é feita através da **API pública de estatísticas do Recorder**
  (`statistics_during_period`), e não por acesso direto à base de dados SQLite.
  Isto torna a integração mais robusta a alterações de schema do Home Assistant.
- A consulta corre no **executor da base de dados do Recorder** (não bloqueia o
  event loop) e a unidade é convertida automaticamente para **kWh**.
- O intervalo de atualização é de **30 minutos**.
- Requer que o sensor configurado produza estatísticas de longo prazo no Recorder
  e que o componente `recorder` esteja ativo.

---

## 📁 Estrutura

```
pt_energy_consumption_sensor/
├── __init__.py          # Setup/unload e reload ao alterar opções
├── config_flow.py       # Fluxo de configuração e painel de opções
├── const.py             # Constantes, chaves de config e valores por defeito
├── sensor.py            # Coordenador do Recorder e entidades
├── manifest.json        # Metadados da integração
├── hacs.json            # Metadados do HACS
├── brand/               # Ícones e logos locais (HA 2026.3+)
├── translations/        # Traduções (en, pt)
├── README.md
├── CHANGELOG.md         # Histórico de versões (Keep a Changelog)
├── LICENSE
└── .gitignore
```

---

## ⚖️ Aviso legal

Esta integração faz **estimativas** de custo com base nos parâmetros introduzidos
pelo utilizador. **Não substitui a fatura oficial** da sua comercializadora de
energia. Os autores não se responsabilizam por diferenças entre os valores
estimados e os valores faturados.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Ver o ficheiro [LICENSE](LICENSE).
