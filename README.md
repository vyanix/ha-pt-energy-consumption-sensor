# PT Energy Consumption Sensor

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.3%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Integração personalizada para **Home Assistant** que estima o **custo da fatura de
energia elétrica em Portugal** e o **consumo do ciclo de faturação**, a partir de um
sensor de energia acumulada (kWh) — tipicamente um **Shelly EM / Shelly 3EM**.

Destina-se a **consumidores domésticos (Baixa Tensão Normal — BTN)** e suporta as
tarifas **Simples**, **Bi-Horária** e **Tri-Horária**, nos ciclos **Diário** e
**Semanal**.

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
`total_kwh`, `dias_ciclo`, `inicio_ciclo`, `fim_ciclo`, `opcao_tarifaria`,
`ciclo_horario`, o consumo e o custo de cada período horário
(`consumo_vazio_kwh`, `consumo_fora_vazio_kwh`, `consumo_cheio_kwh`,
`consumo_ponta_kwh`, `custo_vazio`, `custo_fora_vazio`, `custo_cheio`,
`custo_ponta`) e `detalhe_custos` (com o detalhe de cada rubrica).

O sensor de consumo expõe `inicio_ciclo`, `fim_ciclo`, `dias_ciclo` e o consumo
de cada período horário, e usa `last_reset` para que as estatísticas de longo
prazo reiniciem a cada ciclo.

---

## ⏱️ Tarifas e períodos horários

A integração suporta as três **opções tarifárias** do mercado português, com os
**períodos horários** e **ciclos** definidos pela ERSE:

| Opção tarifária | Períodos incluídos |
|---|---|
| **Simples** | Preço único (constante 24h/dia) |
| **Bi-Horária** | Vazio (mais barato) · Fora de Vazio (mais caro) |
| **Tri-Horária** | Vazio (mais barato) · Cheio (intermédio) · Ponta (mais caro) |

O **ciclo horário** determina a distribuição das horas:

- **Ciclo Diário** — os horários são iguais em todos os dias da semana.
- **Ciclo Semanal** — distingue dias úteis, sábados e domingos (fins de semana
  têm blocos alargados de Vazio; aos domingos todo o dia é Vazio).

A estação (**verão/inverno**) é determinada automaticamente pela hora legal
(DST). Os horários exatos estão no ficheiro [`tariffs.json`](tariffs.json), que
pode ser atualizado sem alterar o código.

> **Público-alvo: consumidores domésticos (Baixa Tensão Normal — BTN).**
> Nestes contratos, os **feriados seguem o horário do dia da semana em que
> calham**: um feriado a um dia útil tem horário de dia útil, a um sábado tem
> horário de sábado e a um domingo tem horário de domingo. Por isso, a integração
> distingue apenas **dias úteis, sábados e domingos**, sem tratamento especial de
> feriados.

### Períodos aplicáveis e valores devolvidos

Os atributos de custo por período são **sempre devolvidos**; quando um período
não se aplica à opção tarifária escolhida, o valor é **zero**:

| Opção | Vazio | Fora de Vazio | Cheio | Ponta |
|---|---|---|---|---|
| Simples | 0 | 0 | 0 | 0 |
| Bi-Horária | custo | custo | 0 | 0 |
| Tri-Horária | custo | 0 | custo | custo |

> O consumo de cada hora é repartido proporcionalmente pelos períodos que a
> intersectam (ex.: uma hora que começa às 09:00 num dia com mudança às 09:15
> conta 25 % em Cheio e 75 % em Ponta), já que as estatísticas de longo prazo do
> Recorder têm granularidade horária.

---

## 🧮 Como o custo é calculado

O ciclo de faturação começa no **dia configurado** (ex.: dia 11). Os cálculos aplicam:

- **Energia (kWh)** — o preço varia por período horário conforme a opção
  tarifária e o **IVA** é aplicado segundo as regras da ERSE (ver abaixo).
- **Custo de potência/dia** — valor diário × número de dias do ciclo × IVA normal.
- **Tarifa social** — por kWh, com IVA reduzido/normal conforme o escalão.
- **IEC** — imposto especial de consumo por kWh × IVA normal.
- **Taxa audiovisual** — valor fixo × IVA reduzido.
- **Taxa DGEG** — valor fixo × IVA normal.

> Os valores por defeito são apenas um ponto de partida. Ajuste-os aos da sua
> comercializadora e ao seu contrato.

### Regras de IVA na eletricidade

A taxa reduzida de IVA só se aplica a **potências contratadas até 6,9 kVA
(inclusive)**. Acima desse valor, **todo o consumo** é tributado à taxa normal.

| Condição | Plafond mensal com IVA reduzido |
|---|---|
| Potência > 6,9 kVA | **0 kWh** (tudo a IVA normal) |
| Regime geral (≤ 6,9 kVA) | **200 kWh** |
| Família numerosa (5+ elementos, ≤ 6,9 kVA) | **300 kWh** |

As taxas de IVA variam por **região**, selecionável na configuração:

| Região | IVA reduzido | IVA normal |
|---|---|---|
| **Portugal Continental** (predefinição) | 6 % | 23 % |
| Açores | 4 % | 16 % |
| Madeira | 5 % | 22 % |

O plafond é **distribuído proporcionalmente pelo consumo de cada período
horário** (regra da ERSE para as tarifas Bi e Tri-Horária): se consumir 75 % em
Fora de Vazio e 25 % em Vazio, 75 % do plafond é aplicado ao Fora de Vazio e 25 %
ao Vazio — não se esgota primeiro um período e só depois o outro.

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
| Opção tarifária | Simples, Bi-Horária ou Tri-Horária | `bi-horaria` |
| Ciclo horário | Diário ou Semanal | `semanal` |
| Potência contratada (kVA) | Determina o direito a IVA reduzido (≤ 6,9 kVA) | `6.9` |
| Família numerosa | 5 ou mais elementos → plafond de 300 kWh com IVA reduzido | `false` |
| Região (taxas de IVA) | Portugal Continental, Açores ou Madeira | `continente` |
| Custo de energia por kWh — tarifa simples (€) | Preço único (usado na tarifa Simples) | `0.1337` |
| Custo do período Vazio por kWh (€) | Preço do período Vazio | `0.1000` |
| Custo do período Fora de Vazio por kWh (€) | Preço do período Fora de Vazio (Bi-Horária) | `0.2000` |
| Custo do período Cheio por kWh (€) | Preço do período Cheio (Tri-Horária) | `0.1800` |
| Custo do período Ponta por kWh (€) | Preço do período Ponta (Tri-Horária) | `0.2500` |
| Custo de energia por dia (€) | Termo fixo diário de potência | `0.4624` |
| Tarifa social por kWh (€) | Contribuição da tarifa social | `0.0017` |
| Imposto IEC por kWh (€) | Imposto especial de consumo | `0.0010` |
| Taxa audiovisual (€) | Taxa de contribuição audiovisual | `2.85` |
| Taxa DGEG (€) | Taxa da entidade reguladora | `0.07` |

3. Pode alterar tudo mais tarde através da **roda dentada (Opções)** da integração.
   A integração recarrega automaticamente após guardar.

> **Nota:** os preços por período só são usados se a opção tarifária escolhida os
> incluir. Preencha os períodos correspondentes à sua tarifa; os restantes podem
> ficar a `0`.

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
├── tariffs.py           # Lógica das tarifas e períodos horários (ERSE)
├── tariffs.json         # Estrutura das tarifas, períodos e ciclos horários
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
