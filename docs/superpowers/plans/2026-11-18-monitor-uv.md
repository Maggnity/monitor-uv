# Monitor UV — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Coletar UV real (OpenUV autenticada + Open-Meteo) de 5 cidades, guardar no PostgreSQL, expor via API REST FastAPI com Swagger e mostrar numa interface React acessível de 4 telas — tudo subindo com `docker compose up`.

**Architecture:** Um pacote Python (`backend/app`) com três entradas: `api` (FastAPI), `collector` (APScheduler) e `seed` (migrations + seed idempotente). Regras de domínio (escala OMS, pico, melhores horários, estado atual) ficam em módulos puros que recebem `now` como parâmetro, testados sem relógio real. O front (Vite) consome só a API; a escala de cores vive num único arquivo de tokens.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 (sync) + psycopg 3, Alembic, pydantic-settings, httpx, APScheduler 3.10, pytest + respx, ruff · React 18 + TypeScript + Vite + Tailwind CSS + Recharts + Leaflet/react-leaflet + TanStack Query + React Router, Vitest + Testing Library · PostgreSQL 16, Docker Compose, Nginx.

**Spec:** `docs/superpowers/specs/2026-11-18-monitor-uv-design.md`

## Global Constraints

- Prioridade de corte (de baixo para cima): 1 núcleo do teste → 2 Início → 3 Comparar → 4 Mapa/Alertas → 5 Genética. Tasks 1–11 = prioridade 1; Genética (Task 17) é a primeira a cair.
- Código, nomes de tabelas, rotas e campos JSON em **inglês**; interface, README e mensagens de commit em **português do Brasil**.
- Commits: Conventional Commits em português, um por task (ou por passo de commit), terminando com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Identidade: a do `git config` do Fernando.
- Segredos nunca versionados: `.env` no `.gitignore`; `.env.example` versionado com `OPENUV_API_KEY=` vazio e `UV_PROVIDER=openuv`.
- Todo timestamp no banco é `timestamptz` em UTC. "Dia" é sempre o **dia local da cidade** (`city.timezone`).
- Todo dado gerado é marcado `origin='sintetico'` (leituras/resumos) ou `source='simulado'`. Nada estimado/previsto é exposto como medido.
- Escala OMS (rótulos e recomendações verbatim): `low` Baixo "Sem proteção necessária" · `moderate` Moderado "Use protetor solar e óculos" · `high` Alto "Protetor, chapéu, procure sombra" · `very_high` Muito alto "Evite sol entre 10h e 16h" · `extreme` Extremo "Evite exposição; proteção máxima".
- WCAG 2.1 AA: cor nunca é o único indicador (sempre rótulo + ícone), alvos de toque ≥ 44px, contraste de texto ≥ 4.5:1, navegação por teclado, `prefers-reduced-motion` respeitado.
- Número do UV no card: 72–96px no mobile. Fonte Inter. Fundo neutro claro; cor reservada ao nível de UV. Modo escuro é opcional no briefing: fica fora, salvo se sobrar tempo no fim.
- Aviso fixo (Task 17): "Projeto demonstrativo. Não substitui orientação médica."

## Review Focus

1. **Chave OpenUV ausente, inválida (401/403) ou cota estourada (429)** — o coletor registra um aviso e segue vivo; chave vazia cai para `simulado`. Testes na Task 5.
2. **Cidade sem nenhuma leitura** (instalação nova, coletor ainda não rodou) — `/current` responde 200 com `status: "no_data"`, nunca 500; a tela mostra o estado "sem dados". Testes nas Tasks 7 e 13.
3. **Fronteira de dia local** — leitura às 23:30Z (20:30 em SP) pertence ao dia local, não ao dia UTC; Fortaleza e SP usam o próprio fuso. Teste na Task 6.
4. **API fora do ar / erro de rede no navegador** — estado de erro com "Tentar de novo", sem tela branca. Teste na Task 13.
5. **Entradas inválidas na API** — cidade inexistente → 404; mais de 4 cidades no compare → 422; `period` inválido → 422; alerta sem `X-Client-Id` → 400; limite fora de 1–15 → 422. Testes nas Tasks 8–10.

---

## File Structure

```
.
├── docker-compose.yml          # db, migrate, api, collector, web
├── .env.example  .gitignore  README.md
├── .github/workflows/ci.yml
├── docs/  (spec, plan, postman/monitor-uv.postman_collection.json)
├── backend/
│   ├── Dockerfile  pyproject.toml  alembic.ini
│   ├── docker/init-test-db.sql            # cria o banco uv_test
│   ├── migrations/ env.py  versions/0001_core.py  versions/0002_genetics.py
│   ├── app/
│   │   ├── config.py   db.py   models.py   timeutil.py
│   │   ├── domain/ uv_scale.py  daily.py  current.py  synthetic.py
│   │   ├── providers/ base.py  openuv.py  openmeteo.py  simulated.py
│   │   ├── collector/ jobs.py  main.py
│   │   ├── seed/ cities.py  history.py  main.py
│   │   ├── services/ summary.py  cities.py  compare.py  alerts.py
│   │   ├── api/ main.py  deps.py  schemas.py  routes/{health,cities,compare,map,alerts,readings}.py
│   │   └── genetics/ models.py  burn.py  seed.py  routes.py
│   └── tests/ conftest.py  test_*.py
└── frontend/
    ├── Dockerfile  nginx.conf  package.json  vite.config.ts  tailwind.config.ts  index.html
    └── src/
        ├── main.tsx  App.tsx
        ├── theme/ uvScale.ts  contrast.ts
        ├── api/ client.ts  types.ts  hooks.ts
        ├── lib/ clientId.ts  storage.ts  format.ts
        ├── components/ Layout.tsx UvBadge.tsx UvCard.tsx UvTimeline.tsx BestHours.tsx ForecastList.tsx
        │               ProtectionTips.tsx CitySelector.tsx Skeleton.tsx ErrorState.tsx
        │               UvMap.tsx CityCompareTable.tsx CompareChart.tsx CalendarHeatmap.tsx PhototypePicker.tsx
        └── pages/ HomePage.tsx MapPage.tsx ComparePage.tsx AlertsPage.tsx
```

Dados fixos das cidades (seed, Task 2):

| name | state | lat | lng | timezone | station_code | peak_base (simulado) |
|---|---|---|---|---|---|---|
| São Paulo | SP | -23.5505 | -46.6333 | America/Sao_Paulo | SP-01 | 10 |
| Rio de Janeiro | RJ | -22.9068 | -43.1729 | America/Sao_Paulo | RJ-01 | 11 |
| Belo Horizonte | MG | -19.9167 | -43.9345 | America/Sao_Paulo | BH-01 | 11 |
| Curitiba | PR | -25.4284 | -49.2733 | America/Sao_Paulo | CWB-01 | 9 |
| Fortaleza | CE | -3.7319 | -38.5267 | America/Fortaleza | FOR-01 | 13 |

---

### Task 1: Esqueleto do backend, configuração e banco de teste

**Files:**
- Create: `.gitignore`, `.env.example`, `docker-compose.yml` (só serviço `db` por enquanto), `backend/pyproject.toml`, `backend/docker/init-test-db.sql`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/db.py`, `backend/tests/conftest.py`, `backend/tests/test_config.py`

**Interfaces:**
- Produces: `Settings` (pydantic-settings) com `database_url: str`, `uv_provider: Literal["openuv","simulado"] = "openuv"`, `openuv_api_key: str = ""`, `openuv_interval_min: int = 120`, `openmeteo_interval_min: int = 60`, `collect_window_start_hour: int = 6`, `collect_window_end_hour: int = 19`, `cors_origins: list[str] = ["http://localhost:8080","http://localhost:5173"]`; `get_settings() -> Settings` (lru_cache); `Settings.effective_provider` property → `"simulado"` se `uv_provider=="openuv"` e chave vazia. `db.engine`, `db.SessionLocal`, `db.Base` (DeclarativeBase), `db.get_session()` (generator para FastAPI).
- Produces (testes): fixture `session` em `conftest.py` — usa `TEST_DATABASE_URL` (padrão `postgresql+psycopg://uv:uv@localhost:5432/uv_test`), `Base.metadata.create_all` uma vez por sessão de teste, `TRUNCATE ... RESTART IDENTITY CASCADE` em todas as tabelas após cada teste.

- [ ] **Step 1:** `docker-compose.yml` com `db: postgres:16-alpine`, usuário/senha/banco `uv/uv/uv`, porta 5432, volume `pgdata`, healthcheck `pg_isready`, e `backend/docker/init-test-db.sql` montado em `/docker-entrypoint-initdb.d/` com `CREATE DATABASE uv_test;`. `.gitignore` cobre `.env`, `__pycache__`, `.venv`, `node_modules`, `dist`, `.pytest_cache`.
- [ ] **Step 2: Write failing test** `test_effective_provider_falls_back_to_simulado_without_key` — `Settings(database_url="x", uv_provider="openuv", openuv_api_key="").effective_provider == "simulado"`; e `test_effective_provider_keeps_openuv_with_key` → `"openuv"`.
- [ ] **Step 3:** Run `cd backend && pytest tests/test_config.py -v` → FAIL (import error).
- [ ] **Step 4:** Implementar `config.py` e `db.py`; `pyproject.toml` com dependências do Tech Stack, `[tool.pytest.ini_options] pythonpath=["."]`, ruff configurado (line-length 100).
- [ ] **Step 5:** `docker compose up -d db && cd backend && pip install -e ".[dev]" && pytest -v` → PASS.
- [ ] **Step 6: Commit** `chore: estrutura inicial do backend e banco PostgreSQL no compose`

---

### Task 2: Modelos, migration inicial e seed de cidades

**Files:**
- Create: `backend/app/models.py`, `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/versions/0001_core.py`, `backend/app/seed/cities.py`, `backend/tests/test_seed_cities.py`

**Interfaces:**
- Consumes: `db.Base`, `get_settings().database_url`.
- Produces: modelos `City`, `UvReading`, `UvForecastHourly`, `UvForecastDaily`, `UvDailySummary`, `Alert`, `AlertTrigger` exatamente com as colunas, UNIQUEs, índice e CHECK da tabela 5.1 do spec, mais: `UvReading.uv_max numeric(4,2) null`, `UvReading.uv_max_at timestamptz null` (spec 5.0). `UvDailySummary` PK composta `(city_id, date)`; `origin` ∈ {`real`,`sintetico`}. `Alert.threshold numeric(4,1)` com CHECK `threshold BETWEEN 1 AND 15`. `seed_cities(session) -> int` (upsert por `station_code`, retorna nº de cidades; idempotente).

- [ ] **Step 1: Write failing test** `test_seed_cities_is_idempotent` — chamar `seed_cities` duas vezes → `session.query(City).count() == 5`; Fortaleza tem `timezone == "America/Fortaleza"`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implementar modelos, migration `0001_core` (escrita à mão, espelhando os modelos) e `seed_cities` com a tabela de cidades deste plano.
- [ ] **Step 4:** Run `pytest -v` → PASS. Run `DATABASE_URL=postgresql+psycopg://uv:uv@localhost:5432/uv alembic upgrade head && alembic downgrade base && alembic upgrade head` → sem erro.
- [ ] **Step 5: Commit** `feat(db): modelos, migration inicial e seed das cidades`

---

### Task 3: Escala OMS e utilitários de tempo

**Files:**
- Create: `backend/app/domain/uv_scale.py`, `backend/app/timeutil.py`, `backend/tests/test_uv_scale.py`, `backend/tests/test_timeutil.py`

**Interfaces:**
- Produces: `UvLevel` (dataclass frozen: `key: str, label: str, recommendation: str`); `classify(uv: float) -> UvLevel` — arredonda meio para cima ao inteiro (`math.floor(uv + 0.5)`) e aplica 0–2/3–5/6–7/8–10/11+; `ValueError` se `uv < 0`. `local_date(dt_utc: datetime, tz: str) -> date`; `local_now(now_utc, tz) -> datetime`; `local_day_bounds_utc(d: date, tz: str) -> tuple[datetime, datetime]`.

- [ ] **Step 1: Write failing tests**
```python
@pytest.mark.parametrize("uv,key", [(0,"low"),(2.4,"low"),(2.5,"moderate"),(5.49,"moderate"),
    (5.5,"high"),(7.49,"high"),(7.5,"very_high"),(10.49,"very_high"),(10.5,"extreme"),(14,"extreme")])
def test_classify_boundaries(uv, key): assert classify(uv).key == key
def test_classify_copy(): assert classify(9).recommendation == "Evite sol entre 10h e 16h" and classify(9).label == "Muito alto"
def test_classify_negative_raises(): pytest.raises(ValueError, classify, -0.1)
def test_local_date_uses_city_timezone():
    assert local_date(datetime(2026,11,19,2,30,tzinfo=UTC), "America/Sao_Paulo") == date(2026,11,18)
```
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar (`zoneinfo`). **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(domain): classificação do índice UV pela escala da OMS`

---

### Task 4: Provedores de dados (OpenUV, Open-Meteo, simulado)

**Files:**
- Create: `backend/app/providers/base.py`, `openuv.py`, `openmeteo.py`, `simulated.py`, `backend/app/domain/synthetic.py`, `backend/tests/test_providers.py`, `backend/tests/test_synthetic.py`

**Interfaces:**
- Consumes: `City`.
- Produces:
  - `CurrentReading` (dataclass: `measured_at: datetime(UTC)`, `uv: float`, `uv_max: float|None`, `uv_max_at: datetime|None`, `source: str`).
  - `HourlyPoint(forecast_for: datetime UTC, uv: float)`, `DailyPoint(date: date, uv_max: float, weather_code: int|None)`, `Forecast(hourly: list[HourlyPoint], daily: list[DailyPoint], source: str)`.
  - `class ProviderError(Exception)` com `status: int|None`.
  - `OpenUvProvider(api_key, client: httpx.Client).fetch_current(city) -> CurrentReading` — `GET https://api.openuv.io/api/v1/uv` params `lat`, `lng`; header `x-access-token`; lê `result.uv`, `result.uv_time`, `result.uv_max`, `result.uv_max_time`; status ≠ 200 → `ProviderError(status)`.
  - `OpenMeteoProvider(client).fetch_forecast(city) -> Forecast` — `GET https://api.open-meteo.com/v1/forecast` params `latitude`, `longitude`, `hourly=uv_index`, `daily=uv_index_max,weather_code`, `timezone=city.timezone`, `forecast_days=5`; horários locais convertidos para UTC.
  - `domain/synthetic.py`: `bell_uv(local_hour: float, peak: float) -> float` = `peak * exp(-((h-12.25)**2)/(2*2.3**2))` para `6 <= h <= 19`, senão `0`, arredondado a 2 casas; `seasonal_peak(peak_base: float, lat: float, d: date, rng: random.Random) -> float` — fator sazonal `1 + A*cos(2π*(doy-355)/365)` com `A = 0.08` se `abs(lat) < 10`, `0.35` se `abs(lat) > 24`, senão `0.25`; ruído multiplicativo uniforme ±10%; mínimo 0. `PEAK_BASE: dict[str, float]` por `station_code` (tabela deste plano).
  - `SimulatedProvider(rng_seed: int = 42)` com `fetch_current(city, now_utc)` e `fetch_forecast(city, now_utc)`, usando `bell_uv`; `source="simulado"`.

- [ ] **Step 1: Write failing tests** (respx para HTTP):
  - `test_openuv_sends_key_header_and_dynamic_coords` — rota mock em `api.openuv.io/api/v1/uv` captura request; assert `request.headers["x-access-token"] == "k"`, `params["lat"] == "-23.5505"`, retorno `uv == 3.2`, `uv_max == 10.1`.
  - `test_openuv_raises_provider_error_on_401` e `..._on_429` → `ProviderError.status` 401/429.
  - `test_openmeteo_parses_hourly_and_daily_to_utc` — fixture JSON com `hourly.time=["2026-11-18T12:00"]`, `uv_index=[9.5]`, timezone SP → `forecast_for == datetime(2026,11,18,15,0,tzinfo=UTC)`; daily `weather_code` preservado.
  - `test_bell_uv_zero_at_night_and_peak_near_noon` — `bell_uv(3,10)==0`, `bell_uv(12.25,10)==10`, `bell_uv(20,10)==0`.
  - `test_seasonal_peak_fortaleza_stays_between_11_and_14` — para 365 dias de 2026 com `rng=Random(1)`, `11 <= seasonal_peak(13, -3.73, d, rng) <= 14.5` em todos.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(providers): clientes OpenUV (com chave) e Open-Meteo, e provedor simulado`

---

### Task 5: Coletor agendado

**Files:**
- Create: `backend/app/collector/jobs.py`, `backend/app/collector/main.py`, `backend/tests/test_collector.py`

**Interfaces:**
- Consumes: provedores (Task 4), modelos, `Settings.effective_provider`, `timeutil`, `refresh_summary` (Task 6 — chamada no fim de `collect_current`; até a Task 6 existir, a Task 5 a importa de `app.services.summary` criando o stub `def refresh_summary(session, city, d): pass` que a Task 6 substitui), `evaluate_alerts` (Task 10 — mesma estratégia de stub em `app.services.alerts`).
- Produces: `in_collect_window(now_utc, city, settings) -> bool` (hora local em `[start, end]`); `collect_current(session, provider, now_utc, settings) -> int` (nº de leituras gravadas; ignora cidades fora da janela; `ProviderError` → `logger.warning` com cidade e status, continua as demais); `collect_forecast(session, provider, now_utc) -> int`; upserts via `INSERT ... ON CONFLICT DO UPDATE` (leitura: conflito `(city_id, measured_at, source)` → atualiza uv; previsões: atualiza uv e `fetched_at`). `main.py`: monta o provedor a partir de `effective_provider` (loga `WARNING` "OPENUV_API_KEY vazia — usando provedor simulado" quando cai), roda as duas coletas uma vez na subida e agenda com `BlockingScheduler`: atual a cada `openuv_interval_min`, previsão a cada `openmeteo_interval_min`. Previsão sempre via Open-Meteo, exceto no modo simulado (usa `SimulatedProvider`).

- [ ] **Step 1: Write failing tests** (provedores falsos em memória):
  - `test_collect_current_skips_cities_outside_window` — `now` = 05:00 local SP → 0 leituras; Fortaleza também fora.
  - `test_collect_current_is_idempotent_for_same_timestamp` — rodar duas vezes com o mesmo `measured_at` → 1 linha por cidade.
  - `test_collect_current_survives_provider_error` — provedor levanta `ProviderError(429)` para São Paulo e retorna valor para as outras → 4 leituras, warning em `caplog`.
  - `test_collect_forecast_upserts_latest_value` — duas coletas com valores diferentes para a mesma hora → 1 linha com o valor da segunda.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(collector): coleta agendada de UV atual e previsão com upsert`

---

### Task 6: Resumo diário e histórico sintético idempotente

**Files:**
- Create: `backend/app/services/summary.py` (substitui o stub), `backend/app/seed/history.py`, `backend/app/seed/main.py`, `backend/tests/test_summary.py`, `backend/tests/test_seed_history.py`

**Interfaces:**
- Consumes: `bell_uv`, `seasonal_peak`, `PEAK_BASE`, `local_day_bounds_utc`.
- Produces:
  - `refresh_summary(session, city, d: date) -> None` — se há leitura `origin='real'` no dia local: `uv_max = max(max(uv), max(uv_max))`, `hours_above_8` = nº de horas da previsão horária daquele dia com `uv >= 8` (documentado como estimado), `origin='real'`; senão, se há leituras sintéticas, mesma conta sobre elas com `origin='sintetico'`; upsert em `uv_daily_summary` (real sobrescreve sintético; sintético nunca sobrescreve real).
  - `seed_history(session, today_local: date, days_hourly: int = 30, days_daily: int = 365) -> int` — para cada cidade e cada dia de `today-days_daily` até `today-1` **sem** resumo existente: grava `UvDailySummary` sintético (`uv_max = seasonal_peak`, `hours_above_8` = horas da curva ≥ 8); para os últimos `days_hourly` dias também grava 14 leituras horárias (6h–19h) `source='simulado', origin='sintetico'`. RNG determinístico por `(station_code, date)`. Nunca toca dias ≥ hoje nem dias com dado real. Retorna nº de dias criados.
  - `seed/main.py`: `python -m app.seed.main` roda `alembic upgrade head`, `seed_cities`, `seed_history(today em America/Sao_Paulo)` e (quando existir) seed da genética.

- [ ] **Step 1: Write failing tests**
  - `test_seed_history_stops_at_yesterday` — `seed_history(s, date(2026,11,18))` → nenhum resumo com `date >= 2026-11-18`; existe resumo de `2026-11-17` e de `2025-11-18`.
  - `test_seed_history_is_idempotent` — segunda chamada retorna `0`.
  - `test_seed_history_does_not_overwrite_real_day` — resumo real em `2026-11-10` com `uv_max=7.7` antes do seed → continua `7.7`, `origin='real'`.
  - `test_refresh_summary_real_wins_over_synthetic` — dia com leituras sintéticas e uma real → `origin == 'real'`.
  - `test_refresh_summary_uses_local_day` — leitura real em `2026-11-19T01:30Z` (22:30 em SP) entra no resumo de `2026-11-18`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(seed): histórico sintético idempotente e resumo diário com prioridade do dado real`

---

### Task 7: Regras do "agora" e do "hoje"

**Files:**
- Create: `backend/app/domain/daily.py`, `backend/app/domain/current.py`, `backend/tests/test_daily.py`, `backend/tests/test_current.py`

**Interfaces:**
- Produces (funções puras, sem banco):
  - `peak_window(points: list[tuple[datetime, float]]) -> PeakWindow|None` — `PeakWindow(start: datetime, end: datetime, uv_max: float)`; janela contígua em torno da hora de máximo com `uv >= 0.9 * max`; `end` = início da última hora + 1h; `None` se máximo `< 0.5`.
  - `best_windows(points, max_uv: float = 2.0) -> list[tuple[datetime, datetime]]` — intervalos contíguos com `uv <= 2`, considerando só horas locais 6–19 (pontos já filtrados pelo chamador).
  - `hours_at_or_above(points, threshold=8.0) -> int`.
  - `CurrentState` dataclass: `status: Literal["ok","stale","night","no_data"]`, `display_uv: float|None`, `display_kind: Literal["measured","estimated"]|None`, `measured_uv`, `measured_at`, `estimated_uv`, `level: UvLevel|None`.
  - `resolve_current(now_utc, tz, last_reading: tuple[datetime, float]|None, estimated_now: float|None, interval_min: int, window: tuple[int,int]) -> CurrentState` — regras do spec 5.0/5.1:
    1. sem leitura e sem estimativa → `no_data`;
    2. valor exibido = medido se idade `< 30 min`, senão estimado (se houver), senão medido;
    3. `night` se valor exibido `< 0.5` e hora local fora de 6–17 (tem precedência sobre `stale`);
    4. `stale` só se hora local dentro de `[window_start, window_end]` + `interval_min` de tolerância e idade da leitura `> 2 * interval_min`.

- [ ] **Step 1: Write failing tests**
  - `test_peak_window_formats_plateau` — pontos 10h:8, 11h:10.5, 12h:11, 13h:10, 14h:7 → `start=11h`, `end=14h`, `uv_max=11`.
  - `test_best_windows_morning_and_evening` — 6h:0.5, 7h:1.8, 8h:3 … 17h:2.5, 18h:1.2 → `[(6h,8h),(18h,19h)]`.
  - `test_current_prefers_fresh_measurement` — leitura de 10 min atrás → `display_kind=="measured"`, `status=="ok"`.
  - `test_current_uses_estimate_when_measurement_old` — leitura de 90 min, estimado 9.1 → `display_uv==9.1`, `display_kind=="estimated"`, `status=="ok"`.
  - `test_current_night_has_precedence_over_stale` — 23h local, leitura de 7h atrás, estimado 0 → `night`.
  - `test_current_stale_inside_window` — 14h local, leitura de 5h atrás, sem estimativa → `stale`, `display_uv` = valor medido.
  - `test_current_no_data` → `no_data`, `level is None`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(domain): regras de UV atual, pico e melhores horários`

---

### Task 8: API — app, saúde, cidades, atual, hoje e previsão

**Files:**
- Create: `backend/app/api/main.py`, `deps.py`, `schemas.py`, `routes/health.py`, `routes/cities.py`, `backend/app/services/cities.py`, `backend/tests/test_api_cities.py`

**Interfaces:**
- Consumes: `resolve_current`, `peak_window`, `best_windows`, `hours_at_or_above`, `classify`, `get_session`.
- Produces:
  - `app = FastAPI(title="Monitor UV API", version="1.0.0")`, routers sob `/api/v1`, CORS de `settings.cors_origins`, Swagger em `/docs` com descrição e exemplos nos schemas. `deps.get_now() -> datetime` (UTC) sobrescrevível nos testes via `app.dependency_overrides`.
  - Schemas: `LevelOut{key,label,recommendation}`, `CityOut{id,name,state,lat,lng,timezone,station_code}`, `CurrentOut{city: CityOut, status, display_uv, display_kind, measured_uv, measured_at, estimated_uv, level: LevelOut|None, next_peak: {date, uv_max, start, end}|None}` (`next_peak` preenchido quando `status=="night"`: pico de amanhã se hora local ≥ 18, senão de hoje), `TodayOut{date, hourly:[{time, uv, level_key}], peak:{start,end,uv_max}|None, best_windows:[{start,end}], hours_above_8, kind:"forecast"}`, `ForecastDayOut{date, uv_max, level: LevelOut, weather_code}`.
  - Rotas: `GET /health` → `{"status":"ok","database":"ok"}` (SELECT 1; 503 se falhar); `GET /cities?q=` (ILIKE sem acento via `unaccent` não é exigido — comparar em Python normalizando com `unicodedata`); `GET /cities/nearest?lat=&lng=` (haversine); `GET /cities/{id}/current`; `GET /cities/{id}/today` (previsão horária do dia local, 6h–19h); `GET /cities/{id}/forecast` (5 dias a partir de hoje). Cidade inexistente → 404 `{"detail":"Cidade não encontrada"}`.

- [ ] **Step 1: Write failing tests** (TestClient + sessão de teste + `get_now` fixo `2026-11-18T17:00Z` = 14h em SP):
  - `test_cities_autocomplete_ignores_accents` — `?q=sao` → contém "São Paulo".
  - `test_nearest_city` — `lat=-3.8&lng=-38.5` → Fortaleza.
  - `test_current_no_data_returns_200` — sem leituras nem previsão → 200, `status=="no_data"`.
  - `test_current_measured` — leitura real de 10 min atrás com uv 9 → `display_kind=="measured"`, `level.key=="very_high"`.
  - `test_today_returns_peak_and_best_windows` — previsão horária inserida → `peak.uv_max` e `best_windows` coerentes; `kind=="forecast"`.
  - `test_unknown_city_404`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(api): endpoints de cidades, UV atual, linha do tempo e previsão`

---

### Task 9: API — histórico, comparação, CSV e mapa

**Files:**
- Create: `backend/app/services/compare.py`, `backend/app/api/routes/compare.py`, `backend/app/api/routes/map.py`, `backend/tests/test_api_compare.py`
- Modify: `backend/app/api/routes/cities.py` (adiciona history)

**Interfaces:**
- Consumes: `UvDailySummary`, previsões, `resolve_current`, `peak_window`, `hours_at_or_above`.
- Produces:
  - `GET /cities/{id}/history?period=7d|30d|12m` → `{period, contains_synthetic: bool, days:[{date, uv_max, level_key, origin}]}` (dias passados até ontem + hoje previsto marcado `origin="forecast"`); `period` inválido → 422.
  - `CompareRow{city: CityOut, current_uv, current_kind, peak_today, hours_above_8, trend: "up"|"down"|"stable", sparkline: list[float]}` — `trend`: máx. previsto de hoje vs média de `uv_max` dos 7 dias anteriores, diferença `> 0.5` → up, `< -0.5` → down; `sparkline` = 7 dias anteriores + hoje.
  - `GET /compare?city_ids=1,2&date=YYYY-MM-DD` → `{date, contains_synthetic, rows: list[CompareRow] (todas as cidades), series: [{city_id, points:[{time, uv}]}] (só as de city_ids; padrão: as 4 primeiras por id)}`; `city_ids` com mais de 4 → 422. Série: data de hoje → previsão horária; data passada → leituras (real vence sintético), preenchendo com previsão se faltar.
  - `GET /compare/export.csv?date=` → `text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="comparativo-uv-<date>.csv"`, cabeçalho `cidade,uf,data,uv_atual,tipo_uv_atual,pico_previsto,horas_acima_de_8,tendencia`.
  - `GET /map?when=now|peak_today|tomorrow` → `[{city_id, name, lat, lng, uv, level: LevelOut, kind: "measured"|"estimated"|"forecast"}]`.

- [ ] **Step 1: Write failing tests**
  - `test_history_flags_synthetic` — após `seed_history` → `contains_synthetic is True`, `len(days)` = 7 + 1 para `7d`.
  - `test_history_invalid_period_422`.
  - `test_compare_rejects_more_than_4_cities` → 422.
  - `test_compare_trend_up` — resumos dos 7 dias com `uv_max=6`, previsão de hoje com máx. 9 → `trend=="up"`.
  - `test_export_csv_header_and_rows` — primeira linha igual ao cabeçalho acima; 5 linhas de dados.
  - `test_map_tomorrow_uses_daily_forecast` → `kind=="forecast"`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(api): histórico, comparação entre cidades, exportação CSV e mapa`

---

### Task 10: API — leituras paginadas e alertas

**Files:**
- Create: `backend/app/services/alerts.py` (substitui o stub), `backend/app/api/routes/alerts.py`, `backend/app/api/routes/readings.py`, `backend/tests/test_api_alerts.py`, `backend/tests/test_api_readings.py`

**Interfaces:**
- Produces:
  - `GET /readings?city_id=&from=&to=&origin=&page=1&page_size=50` (`page_size ≤ 200`) → `{items:[{id, city_id, measured_at, uv_index, source, origin}], page, page_size, total}`, ordenado por `measured_at desc`.
  - Header `X-Client-Id` (UUID) obrigatório em `/alerts*` → ausente/inválido: 400 `{"detail":"Header X-Client-Id obrigatório"}`.
  - `GET /alerts`, `POST /alerts {city_id, threshold}` (threshold 1–15 → senão 422; cidade inexistente → 404), `PATCH /alerts/{id} {active?, threshold?}`, `DELETE /alerts/{id}` (204); alerta de outro client → 404. `AlertOut{id, city: CityOut, threshold, active, created_at, last_triggered_at}`.
  - `GET /alerts/triggers?since=` (padrão: início do dia local SP) → `[{alert_id, city_name, threshold, uv, triggered_at}]`.
  - `evaluate_alerts(session, reading: UvReading, city: City) -> int` — dispara alertas ativos da cidade com `reading.uv_index > threshold`, no máximo 1 disparo por alerta por dia local; retorna nº de disparos.

- [ ] **Step 1: Write failing tests**
  - `test_alerts_require_client_id` → 400.
  - `test_alert_threshold_out_of_range` → 422 para 0 e 16.
  - `test_alerts_isolated_by_client` — alerta do client A não aparece/patcha para B (404).
  - `test_evaluate_alerts_once_per_day` — duas leituras acima do limite no mesmo dia → 1 disparo; leitura igual ao limite (8 com limite 8) → 0.
  - `test_readings_pagination` — 120 leituras, `page_size=50&page=3` → 20 itens, `total==120`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(api): consulta paginada de leituras e CRUD de alertas com disparo`

---

### Task 11: Docker Compose completo do backend

**Files:**
- Create: `backend/Dockerfile`, `backend/.dockerignore`
- Modify: `docker-compose.yml`, `.env.example`

**Interfaces:**
- Produces: imagem `backend` (python:3.12-slim, usuário não-root, `pip install .`); serviços `migrate` (`python -m app.seed.main`, `restart: "no"`, depende de `db` healthy), `api` (`uvicorn app.api.main:app --host 0.0.0.0 --port 8000`, depende de `migrate` `service_completed_successfully`, healthcheck em `/api/v1/health`), `collector` (`python -m app.collector.main`, depende de `migrate`). Todos leem `env_file: .env` (com `required: false`) e têm defaults para rodar sem `.env` (provedor simulado). `.env.example` documenta cada variável com comentário.

- [ ] **Step 1:** Escrever Dockerfile e compose.
- [ ] **Step 2: Verify** a partir do zero (`docker compose down -v`): `docker compose up -d --build && sleep 20 && curl -s localhost:8000/api/v1/health` → `{"status":"ok","database":"ok"}`; `curl -s localhost:8000/api/v1/cities | jq length` → `5`; `curl -s "localhost:8000/api/v1/cities/1/history?period=12m" | jq .contains_synthetic` → `true`; `docker compose logs collector` mostra o aviso de provedor simulado (sem `.env`) e leituras gravadas.
- [ ] **Step 3: Verify com chave real** (se o Fernando já tiver `OPENUV_API_KEY` no `.env`): `docker compose restart collector` e `curl -s "localhost:8000/api/v1/readings?origin=real" | jq .total` > 0 dentro da janela 6h–19h.
- [ ] **Step 4: Commit** `build(docker): imagens e compose com banco, migrações, API e coletor`

---

### Task 12: Front — base, tokens da escala e navegação

**Files:**
- Create: `frontend/` (Vite React-TS), `tailwind.config.ts`, `src/theme/uvScale.ts`, `src/theme/contrast.ts`, `src/api/client.ts`, `src/api/types.ts`, `src/api/hooks.ts`, `src/lib/clientId.ts`, `src/lib/storage.ts`, `src/lib/format.ts`, `src/components/Layout.tsx`, `Skeleton.tsx`, `ErrorState.tsx`, `UvBadge.tsx`, `src/App.tsx`, testes `src/theme/uvScale.test.ts`, `src/lib/format.test.ts`, `frontend/Dockerfile`, `frontend/nginx.conf`
- Modify: `docker-compose.yml` (serviço `web` em `8080:80`, depende de `api`)

**Interfaces:**
- Produces:
  - `uvScale.ts`: `UvLevelKey = "low"|"moderate"|"high"|"very_high"|"extreme"`; `UV_LEVELS: Record<UvLevelKey, {label, bg, fg, icon, range: [number, number|null]}>` — valores iniciais `bg/fg`: low `#2E7D32/#FFFFFF`, moderate `#F9D71C/#1A1A1A`, high `#EF6C00/#1A1A1A`, very_high `#C62828/#FFFFFF`, extreme `#6A1B9A/#FFFFFF` (ajustar se o teste falhar); `levelFromUv(uv: number): UvLevelKey` (mesma regra de arredondamento do backend, só para gráficos/mapa onde a API manda número cru).
  - `contrast.ts`: `contrastRatio(hexA, hexB): number` (WCAG relative luminance).
  - `client.ts`: `apiGet<T>(path, init?)`, `apiSend<T>(method, path, body?)` com base `/api/v1`, header `X-Client-Id` automático, lança `ApiError{status, message}`; `types.ts` espelha os schemas das Tasks 8–10.
  - `hooks.ts` (TanStack Query, `refetchInterval` 5 min para current/today): `useCities(q)`, `useCurrent(cityId)`, `useToday(cityId)`, `useForecast(cityId)`, `useHistory(cityId, period)`, `useCompare(cityIds, date)`, `useMap(when)`, `useAlerts()`, `useAlertTriggers()`, mutations de alertas.
  - `format.ts`: `relativeTime(iso, now): string` ("agora mesmo", "há 4 min", "há 2 h"); `hourLabel(iso, tz)` ("11h", "12h30"); `peakLabel(start,end,uv)` → `"Pico: 11 às 12h30"`.
  - `Layout`: navegação inferior fixa no mobile (`< md`) e barra lateral no desktop, itens Início/Mapa/Comparar/Alertas com ícone + texto, `aria-current`, alvos ≥ 44px, link "Pular para o conteúdo". Rotas `/`, `/mapa`, `/comparar`, `/alertas`.
  - `UvBadge({uv, levelKey, size})`: chip com cor, ícone e rótulo em texto. `Skeleton`, `ErrorState({message, onRetry})` com botão "Tentar de novo".
  - Dev: `vite.config.ts` com proxy `/api → http://localhost:8000`. Prod: `nginx.conf` serve `dist` com fallback SPA e `location /api/ { proxy_pass http://api:8000; }`.

- [ ] **Step 1: Write failing tests**
  - `every UV level keeps text contrast >= 4.5` — para cada nível, `contrastRatio(bg, fg) >= 4.5`.
  - `levelFromUv boundaries` — 2.4 → low, 2.5 → moderate, 10.5 → extreme.
  - `relativeTime` — 4 min → "há 4 min"; `peakLabel` → "Pico: 11 às 12h30".
- [ ] **Step 2:** `npm test` → FAIL. **Step 3:** Implementar. **Step 4:** `npm test` → PASS; `npm run build` sem erro de tipo.
- [ ] **Step 5: Verify** `docker compose up -d --build web` → `http://localhost:8080` mostra o layout com as 4 abas navegáveis por Tab.
- [ ] **Step 6: Commit** `feat(web): base do front, tokens da escala OMS e navegação responsiva`

---

### Task 13: Tela Início com todos os estados

**Files:**
- Create: `src/pages/HomePage.tsx`, `src/components/CitySelector.tsx`, `UvCard.tsx`, `UvTimeline.tsx`, `BestHours.tsx`, `ForecastList.tsx`, `ProtectionTips.tsx`, testes `src/components/UvCard.test.tsx`, `src/pages/HomePage.test.tsx`

**Interfaces:**
- Consumes: hooks, `UV_LEVELS`, `format.ts`, `storage.ts` (`getCityId()/setCityId()`, `hasAskedLocation()/markAskedLocation()`).
- Produces:
  - `CitySelector` — combobox acessível (ARIA 1.2) com autocomplete e botão "Usar minha localização" (`navigator.geolocation` → `/cities/nearest`).
  - Primeiro acesso: se `!hasAskedLocation()`, cartão "Usamos sua localização só para mostrar o UV da cidade mais próxima." com "Permitir" / "Escolher cidade". Negado/erro → São Paulo.
  - `UvCard({current})` — estados: `ok` (número 72–96px, rótulo, ícone, recomendação, "atualizado há X" ou "estimado agora · última medição há X"), `stale` (valor com selo "Desatualizado" + horário da última medição), `night` ("O sol já se pôs. UV zero agora." + "Amanhã o pico deve chegar a N, das Xh às Yh"), `no_data` ("Ainda não temos leituras para esta cidade"). Fundo = `bg` do nível; transição de cor/número desativada com `prefers-reduced-motion`.
  - `UvTimeline({today, now})` — Recharts `AreaChart` 6h–19h, `ReferenceArea` com as faixas da escala em baixa opacidade, `ReferenceLine` "agora", rótulo do pico via `peakLabel`, tooltip; legenda textual do pico para leitor de tela.
  - `BestHours` — "Melhores horários para sair" com os intervalos; vazio → "Hoje não há períodos com UV baixo entre 6h e 19h".
  - `ForecastList` — 5 dias: dia da semana, ícone do tempo (mapa `weather_code → ícone + texto`), `UvBadge` do máximo.
  - `ProtectionTips` — `<details>` com dicas conforme o nível atual.
  - Carregando: skeletons por bloco. Erro: `ErrorState` por bloco com `refetch`.

- [ ] **Step 1: Write failing tests** (Testing Library, dados mockados com MSW ou mock do `fetch`):
  - `UvCard ok shows big number, label and recommendation` — uv 9 → texto "9", "Muito alto", "Evite sol entre 10h e 16h".
  - `UvCard estimated labels value as estimated` → contém "estimado".
  - `UvCard night shows tomorrow peak`.
  - `UvCard stale shows Desatualizado`.
  - `HomePage shows retry on network error` — fetch rejeita → botão "Tentar de novo"; clicar dispara novo fetch.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Verify** no navegador (390×844 e 1280×800): card, linha do tempo com marcador do agora, melhores horários, 5 dias, dicas; desligar a API (`docker compose stop api`) → estado de erro e retry funciona ao religar.
- [ ] **Step 6: Commit** `feat(web): tela Início com card de UV, linha do tempo, previsão e estados`

---

### Task 14: Tela Comparar cidades

**Files:**
- Create: `src/pages/ComparePage.tsx`, `src/components/CityCompareTable.tsx`, `CompareChart.tsx`, `CalendarHeatmap.tsx`, teste `src/components/CityCompareTable.test.tsx`

**Interfaces:**
- Consumes: `useCompare`, `useHistory`.
- Produces: `CityCompareTable({rows})` — `<table>` ordenável por coluna (botões no `<th>` com `aria-sort`), colunas Cidade, UV atual (`UvBadge` + "estimado" quando for o caso), Pico previsto, Horas acima de 8, Tendência (seta + texto "subindo/caindo/estável" + sparkline Recharts sem eixos). `CompareChart` — seleção de até 4 cidades (checkboxes; 5ª desabilitada com dica), `LineChart` por hora. `CalendarHeatmap({days})` — grade dias × semanas em SVG, cor pelo nível, `title`/`aria-label` com data e UV; seletor 7d/30d/12m e de cidade. Aviso discreto "Inclui dados sintéticos de demonstração" quando `contains_synthetic`. Botão "Exportar CSV" → link para `/api/v1/compare/export.csv?date=`.

- [ ] **Step 1: Write failing test** `sorts by peak descending when header clicked twice` — linhas com picos 8, 13, 10 → ordem 13, 10, 8 e `aria-sort="descending"`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Verify** no navegador: ordenação, gráfico com 4 cidades, mapa de calor 12m, CSV baixa e abre no LibreOffice/Excel com acentos corretos.
- [ ] **Step 6: Commit** `feat(web): painel de comparação com tabela, gráfico, histórico e CSV`

---

### Task 15: Tela Mapa

**Files:**
- Create: `src/pages/MapPage.tsx`, `src/components/UvMap.tsx`

**Interfaces:**
- Consumes: `useMap(when)`, `useCurrent`.
- Produces: `UvMap({points, onSelect})` — react-leaflet com tiles OpenStreetMap (atribuição visível), `DivIcon` circular com a cor do nível **e** o número; marcadores focáveis por teclado (Enter abre). Bottom sheet (`role="dialog"`, foco gerenciado, fecha com Esc) com nome, `UvBadge`, recomendação e link "Ver detalhes" → Início com a cidade selecionada. Legenda fixa compacta da escala (cor + rótulo). Filtro segmentado Agora / Pico de hoje / Amanhã. Lista textual das cidades abaixo do mapa como alternativa acessível.

- [ ] **Step 1: Verify** no navegador: 5 marcadores coloridos com número, filtro troca valores, bottom sheet abre por toque e por teclado, Esc fecha, legenda visível no mobile.
- [ ] **Step 2: Commit** `feat(web): mapa das cidades com marcadores por nível e painel inferior`

---

### Task 16: Tela Alertas

**Files:**
- Create: `src/pages/AlertsPage.tsx`, teste `src/pages/AlertsPage.test.tsx`
- Modify: `src/pages/HomePage.tsx` (banner de disparo do dia)

**Interfaces:**
- Consumes: `useAlerts`, mutations, `useAlertTriggers`, `clientId`.
- Produces: formulário "Me avise quando o UV passar de [N] em [cidade]" (select de cidade, input numérico 1–15 com stepper ≥ 44px), lista de alertas com interruptor (`role="switch"`, `aria-checked`) e excluir, seção "Disparos recentes". Banner no Início: "Alerta: UV passou de 8 em Fortaleza às 11h" quando houver disparo hoje para a cidade exibida.

- [ ] **Step 1: Write failing test** `toggling a switch sends PATCH with active=false` (fetch mockado).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS.
- [ ] **Step 5: Verify** criar alerta com limite baixo (ex.: 1) numa cidade dentro da janela, aguardar/forçar coleta (`docker compose restart collector`) → disparo aparece em Alertas e banner no Início.
- [ ] **Step 6: Commit** `feat(web): tela de alertas com cadastro, interruptor e disparos`

---

### Task 17: Camada genética (cortável)

**Files:**
- Create: `backend/migrations/versions/0002_genetics.py`, `backend/app/genetics/models.py`, `burn.py`, `seed.py`, `routes.py`, `backend/tests/test_genetics.py`, `frontend/src/components/PhototypePicker.tsx`
- Modify: `backend/app/seed/main.py`, `backend/app/api/routes/cities.py` (param `phototype`), `backend/app/services/compare.py` + CSV (coluna `vulnerabilidade_estimada`), `frontend/src/components/UvCard.tsx`, `CityCompareTable.tsx`, `Layout.tsx` (aviso fixo)

**Interfaces:**
- Produces:
  - Tabelas `skin_phototype(code PK, description, med_j_m2, source)` e `city_phototype_distribution(city_id, phototype, share, source, is_illustrative)`, PK `(city_id, phototype)`.
  - Seed MED (J/m², eritêmica): I 200, II 250, III 300, IV 450, V 600, VI 1000 — `source = "Valores típicos citados na literatura (Fitzpatrick, 1988; Diffey, 1991)"`. Descrições leigas: I "Pele muito clara, sempre queima, nunca bronzeia" … VI "Pele negra, nunca queima".
  - Distribuição ilustrativa (I..VI), `is_illustrative=true`: SP `.05,.20,.30,.25,.15,.05` · RJ `.03,.15,.30,.27,.18,.07` · BH `.03,.15,.30,.27,.18,.07` · Curitiba `.08,.30,.32,.18,.09,.03` · Fortaleza `.02,.10,.25,.33,.22,.08`.
  - `minutes_to_burn(uv: float, med_j_m2: float) -> int|None` = `round(med / (uv * 0.025) / 60)`; `None` se `uv < 0.5`.
  - `GET /phototypes`; `GET /cities/{id}/current?phototype=III` adiciona `minutes_to_burn` (calculado sobre `display_uv`); fototipo inválido → 422. `CompareRow.vulnerability = round(peak_today * share(I+II+III), 1)` + `vulnerability_illustrative: true`.
  - Front: `PhototypePicker` (linha opcional "Seu tipo de pele", radios I–VI com descrição, salvo em `storage`), card mostra "Você pode se queimar em cerca de N min agora"; texto "O fototipo tem forte componente genético (ex.: variantes do gene MC1R)."; coluna "Vulnerabilidade estimada (ilustrativa)" em Comparar; rodapé fixo "Projeto demonstrativo. Não substitui orientação médica."

- [ ] **Step 1: Write failing tests**
  - `test_minutes_to_burn_type_ii_uv10` → `17` (250 / 0.25 / 60 = 16.67).
  - `test_minutes_to_burn_none_at_night` → `None` para uv 0.
  - `test_current_with_phototype` → campo `minutes_to_burn` presente; `phototype=VII` → 422.
  - `test_compare_vulnerability_curitiba` — pico 9 → `round(9*0.70,1) == 6.3`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implementar. **Step 4:** Run → PASS (backend e front).
- [ ] **Step 5: Commit** `feat(genetica): fototipo, tempo estimado até queimadura e vulnerabilidade ilustrativa`

---

### Task 18: README, Postman e CI

**Files:**
- Create: `README.md`, `docs/postman/monitor-uv.postman_collection.json`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: README em português com: visão geral + diagrama (mermaid) da arquitetura; pré-requisitos (Docker 24+); como obter a chave OpenUV; `cp .env.example .env`; `docker compose up -d --build`; URLs (`http://localhost:8080`, `http://localhost:8000/docs`); seção "Acesso aos dados" com `curl` de `/cities`, `/cities/1/current`, `/readings?city_id=1&page_size=5`, `/compare/export.csv`; modelagem das tabelas (mermaid ER) com justificativas; decisões e trade-offs (duas fontes, cota de 50/dia → 120 min na janela 6h–19h ≈ 35 chamadas, modo simulado, histórico sintético até ontem e prioridade do real, previsto vs medido); fontes científicas e aviso médico (se Task 17 entrou); como rodar testes (backend e front); estrutura de pastas. Coleção Postman com as rotas e variável `baseUrl`. CI: job Python (serviço postgres 16, `ruff check`, `pytest`) e job Node (`npm ci`, `npm test`, `npm run build`).

- [ ] **Step 1: Verify** seguir o README do zero: `docker compose down -v && rm .env` → passos do README → front e Swagger abrem; todos os `curl` respondem.
- [ ] **Step 2: Verify** sintaxe do workflow: `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:latest` → sem erros.
- [ ] **Step 3: Commit** `docs: README com configuração, execução, acesso remoto e decisões`
- [ ] **Step 4:** Perguntar ao Fernando o nome do repositório no GitHub antes de criar e fazer push.
