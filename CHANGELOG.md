# Changelog

Todas as alterações relevantes desta integração são documentadas neste ficheiro.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-PT/1.1.0/)
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt/).

## [Não publicado]

### Planeado
- Suporte a tarifas bi-horárias / tri-horárias (vazio, fora de vazio e ponta).
- Configuração de um segundo sensor de consumo (ex.: produção solar).
- Opção para definir o título do dispositivo e das entidades.

---

## [1.2.0] - 2026-10-05

### Adicionado
- **Novo sensor de consumo** `sensor.consumo_do_ciclo_de_faturacao` (kWh), que
  devolve a energia consumida desde o início do ciclo de faturação, com
  `last_reset` definido para o início do ciclo.
- **Sensor de consumo configurável**: o sensor Shelly (energia acumulada em kWh)
  passa a ser escolhido na configuração através de um seletor de entidades, em
  vez de estar fixo no código.
- **Seletores nos formulários**: `EntitySelector` para o sensor de consumo e
  `NumberSelector` com limites e unidades para os restantes campos.
- **Coordenador de atualização** (`DataUpdateCoordinator`) partilhado pelas duas
  entidades, reduzindo a consulta à base de dados a uma única leitura por ciclo.
- **Atributos de diagnóstico** no sensor de custo: `total_kwh`, `dias_ciclo`,
  `inicio_ciclo`, `fim_ciclo` e `detalhe_custos` (com o detalhe por rubrica).
- **Traduções** (`translations/pt.json` e `translations/en.json`) com títulos
  amigáveis para todos os campos de configuração e opções.
- **Imagens de marca locais** na pasta `brand/` (ícone e logo, em versão normal e
  @2x), suportadas a partir do Home Assistant 2026.3.
- **Documentação**: `README.md` completo, com aviso de requisito obrigatório do
  sensor de energia, instruções de instalação, tabela de parâmetros e resolução
  de problemas.
- **Licença MIT** (`LICENSE`) e ficheiro `.gitignore`.
- **Validação de configuração**: impede guardar sem escolher um sensor de consumo
  (mensagem de erro `missing_sensor`).

### Alterado
- **Leitura de dados migrada para a API pública do Recorder**
  (`statistics_during_period`), substituindo o acesso direto à base de dados
  SQLite. A integração passa a ser robusta a alterações de schema do Home
  Assistant.
- **Consulta executada no executor de base de dados do Recorder**
  (`get_instance(hass).async_add_executor_job`), em vez do executor genérico,
  eliminando o aviso de acesso à BD fora do DB executor e sem bloquear o event loop.
- **Conversão automática de unidades para kWh** (`units={"energy": "kWh"}`),
  funcionando também com sensores em Wh ou MWh.
- **Datas com fuso horário** (`dt_util.now()` / `dt_util.as_utc`) em vez de
  `datetime.datetime.now()` sem timezone.
- **`manifest.json` limpo**: nome alinhado com o repositório, `integration_type`
  definido, versão atualizada para `1.2.0` e remoção de chaves vazias
  (`requirements`, `zeroconf`, `loggers`).
- **`hacs.json`** com versão mínima do Home Assistant e `zip_release`.
- **`__init__.py`** refatorado com constante `PLATFORMS` e comentários claros.
- **`const.py`** centraliza chaves de configuração, valores por defeito e taxas
  de IVA; o valor por defeito do sensor de consumo passou a ser vazio.

### Corrigido
- **Erro 400 ao abrir as Opções** ("O fluxo de configuração não pôde ser
  carregado"): o `step` dos seletores numéricos usava `0.0001`, abaixo do mínimo
  aceite pelo Home Assistant (`0.001`), o que originava um `probatio.Invalid` e
  uma resposta HTTP 400. Passou a usar `step="any"`.
- **`OptionsFlow` incompatível**: removida a atribuição a `self.config_entry` no
  `__init__`, que é uma propriedade só de leitura nas versões recentes do HA.
- **Cálculo do início do ciclo em meses curtos**: o dia de início é limitado ao
  último dia do mês (ex.: dia 31 em fevereiro), evitando `ValueError`.
- **`state_class` do sensor monetário**: corrigido de `MEASUREMENT` para `TOTAL`,
  que é o único estado permitido para `device_class: monetary`.
- **Consumo do primeiro dia do ciclo**: a leitura por `change` horário passa a
  contabilizar corretamente o consumo desde o início exato do ciclo.

### Segurança
- **Removido o identificador pessoal** do Shelly que estava fixo no código
  (`statistic_id` por defeito). O sensor passa a ser obrigatoriamente escolhido
  pelo utilizador.
- **Eliminado o risco de injeção de SQL** associado à construção de consultas por
  interpolação de strings.

### Removido
- `logo.png` e `logo.svg` da raiz da integração (substituídos pela pasta
  `brand/`).
- `strings.json` (não é utilizado por integrações personalizadas; as traduções
  passam a estar em `translations/`).
- Acesso direto à base de dados `/config/home-assistant_v2.db` e o caminho fixo
  associado.

---

## [1.1.0] - 2026-10-02

### Adicionado
- Versão inicial da integração **PT Energy Consumption Sensor** (Vyanix).
- Sensor `sensor.custo_total_de_energia` (EUR), com o custo estimado da fatura de
  energia para o ciclo de faturação corrente.
- Config flow e painel de opções para definir os parâmetros de faturação.
- Cálculo do ciclo de faturação a partir do dia de início configurável.
- Aplicação de IVA reduzido (6 %) e normal (23 %) conforme o limite de consumo.
- Cálculo das rubricas: termo de energia diário, energia consumida, tarifa
  social, imposto IEC, taxa audiovisual e taxa DGEG.
- Leitura do consumo diretamente da base de dados de estatísticas do Home
  Assistant (`home-assistant_v2.db`).
- Atualização automática a cada 30 minutos.
- Dispositivo virtual *Vyanix Power Monitor*.

[1.2.0]: https://github.com/vyanix/ha-pt-energy-consumption-sensor/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/vyanix/ha-pt-energy-consumption-sensor/releases/tag/v1.1.0
[Não publicado]: https://github.com/vyanix/ha-pt-energy-consumption-sensor/compare/v1.2.0...HEAD
