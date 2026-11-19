# Monitor UV: documento de design

Data: 2026-11-18 · Prazo de entrega: até 2026-11-21 (3 dias de trabalho)

## 1. Intenção e o porquê

Este é o teste técnico do Fernando para a vaga de Desenvolvedor de Software Pleno numa empresa de **análises genéticas**. O teste pede:

1. Extração de dados de uma API pública via GET, com **parâmetros dinâmicos na URL** e **autenticação por chave de API**.
2. Armazenamento num banco relacional (PostgreSQL).
3. Uma API REST simples para consultar os dados, documentada (Swagger).
4. (Opcional) Docker com API e banco, reproduzível em qualquer máquina.
5. Repositório no GitHub organizado, com README explicando configuração, execução e acesso remoto.

Critérios de avaliação: qualidade e clareza do código, organização do Git e da documentação, estrutura correta das tabelas e uso correto do Docker.

Para se destacar, o Fernando escolheu o tema **radiação ultravioleta por cidade**, com uma ponte para a genética (sensibilidade da pele por fototipo). Ele também quer uma **interface web completa**, seguindo um briefing de design que ele forneceu (seção 6).

**Como é o sucesso:** o avaliador clona o repositório, roda um comando, vê dados reais de UV chegando, abre o Swagger e uma interface bonita e acessível, e lê um histórico de commits que conta a construção passo a passo.

## 2. Objetivos, não objetivos e anti-objetivos

### Objetivos (em ordem de prioridade; se o tempo apertar, corta-se de baixo para cima)

1. **Núcleo do teste, impecável:** coletor, banco, API REST, Swagger, Docker Compose e README.
2. **Tela Início completa**, com todos os estados obrigatórios.
3. **Tela Comparar cidades** (painel para gestores).
4. **Telas Mapa e Alertas** funcionais. O acabamento pode ser mais simples se faltar tempo.
5. **Camada genética** (seção 7). É a primeira a cair: decisão do Fernando.

### Não objetivos

- Login, contas ou autenticação de usuários finais.
- Notificações push, e-mail ou SMS para alertas.
- Sensores físicos reais. A "estação" é uma por cidade, abastecida pela API pública.
- Cidades além das 5 do briefing (a modelagem deve permitir adicionar outras por seed/config).

### Anti-objetivos (o projeto falha mesmo funcionando se...)

- **Fizer afirmações médicas ou genéticas sem fonte.** Para uma empresa de genética, exagero científico pesa mais que falta de funcionalidade. Todo número de referência (MED por fototipo, distribuição de fototipos) tem fonte citada no README e é rotulado como estimativa/ilustrativo na interface, com aviso de que o projeto não é orientação médica.
- **Não subir com um comando** numa máquina limpa.
- **Esconder dados sintéticos** como se fossem reais. Todo dado gerado é marcado no banco e na API.
- **Ter um histórico de Git confuso** (commit único gigante, mensagens vagas, segredos commitados).

## 3. Restrições

- Linguagem do backend: **Python** (preferência explícita do teste).
- Banco: **PostgreSQL**.
- A chave de API **nunca** vai para o repositório: fica em `.env` (ignorado), com `.env.example` versionado.
- Prazo: 3 dias.
- O briefing de interface (seção 6) é obrigatório nas partes marcadas como obrigatórias (escala OMS, estados, acessibilidade WCAG 2.1 AA).

## 4. Fontes de dados

### 4.1 OpenUV: fonte autenticada (requisito do teste)

- `GET https://api.openuv.io/api/v1/uv?lat={lat}&lng={lng}` com o header `x-access-token: {OPENUV_API_KEY}`.
- Fornece o UV atual e o UV máximo do dia (com horário do pico) por coordenada. lat/lng vêm da tabela de cidades, que são os parâmetros dinâmicos.
- **Limite do plano gratuito: 50 requisições/dia.** Com 5 cidades, a coleta não pode ser a cada 10 minutos. Decisão: o coletor consulta a OpenUV a cada **120 minutos, só entre 6h e 19h no horário local**, o que dá cerca de 35 chamadas/dia. O intervalo é configurável por variável de ambiente. O README explica a conta.

### 4.2 Open-Meteo: previsão (sem chave)

- `GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&hourly=uv_index&daily=uv_index_max,weather_code&timezone=America/Sao_Paulo&forecast_days=5`
- Fornece a previsão horária de UV (linha do tempo de hoje, melhores horários, pico) e a previsão de 5 dias com código do tempo (ícone). Sem limite prático, então pode ser coletada a cada 60 minutos.
- O README justifica as duas fontes: a OpenUV atende o requisito de autenticação e dá a leitura atual; a Open-Meteo cobre a previsão que a OpenUV gratuita não entrega em 5 dias.

### 4.3 Modo simulado (sem chave)

- `UV_PROVIDER=openuv|simulado`. No modo `simulado`, o coletor gera leituras com a curva em sino do briefing (UV 0 de madrugada, pico entre 11h e 13h, 11 a 14 no Nordeste) e marca tudo como `sintetico`.
- Serve para o avaliador rodar o projeto sem criar conta. O padrão no `.env.example` é `openuv`. Se a chave estiver vazia, o coletor registra um aviso claro no log e cai para o modo simulado.

### 4.4 Histórico sintético

- Nenhuma API gratuita entrega 12 meses de histórico de UV. Na primeira subida, um seed gera **12 meses de UV máximo diário + 30 dias de leituras horárias** para as 5 cidades, com sazonalidade (verão mais alto no Sul/Sudeste; Nordeste alto o ano todo), marcados `origem = 'sintetico'`.
- A interface indica discretamente quando um período contém dados sintéticos.

## 5. Arquitetura

```
docker compose up
├── db         PostgreSQL 16 (volume persistente, healthcheck)
├── migrate    roda migrations (Alembic) + seed, depois encerra
├── api        FastAPI (Uvicorn) em :8000, Swagger em /docs
├── collector  mesmo código Python, processo agendado (APScheduler)
└── web        build do React servido por Nginx em :8080, com /api → api:8000
```

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (sync), Alembic, Pydantic Settings, httpx, APScheduler, pytest. Uma imagem, dois comandos (api e collector).
- **Estrutura de pastas:** `backend/` (app, migrations, tests), `frontend/`, `docker-compose.yml`, `README.md`, `docs/`.
- **Coletor:** cada provedor é uma classe com a mesma interface (`fetch_current(city)`, `fetch_forecast(city)`). Usa retry com backoff em erro de rede, registra falhas no log e não derruba o processo. Grava com upsert para não duplicar leituras.
- **Estação offline:** se a última leitura de uma cidade tiver mais de 2x o intervalo de coleta, a API marca `stale: true`. A interface mostra o último valor válido como desatualizado. *(Decisão do assistente)* `stale` só é avaliado **dentro da janela de coleta** (6h–19h local + 1 intervalo de tolerância). Fora dela vale o estado **Noite**, que tem precedência. Assim não aparece "estação offline" toda madrugada.

### 5.0 Regras de dados (decisões do assistente)

- **"UV agora" no card:** a API devolve a **última leitura medida** (`measured_at`, mostrada como "medido há X min") e também `estimated_now`, que é o valor da previsão horária da Open-Meteo para a hora atual. O card mostra o valor medido quando ele tem menos de 30 min. Se for mais antigo, mostra o estimado com o rótulo "estimado agora · última medição há X". Nada estimado aparece como medido.
- **Pico do dia, horas acima de 8 e tendência:** para **hoje**, saem da **previsão horária** e aparecem rotulados como "previsto". Para **dias passados**, saem de `uv_daily_summary`. Esse resumo é calculado a partir das leituras e, para dias com leitura real, também do `uv_max` informado pela OpenUV, que é gravado em colunas extras (`uv_max`, `uv_max_at`) de `uv_reading`. A tendência compara o UV máximo de hoje (previsto) com a média dos 7 dias anteriores.
- **Convivência entre dados reais e sintéticos:** o seed gera dados **somente até ontem (D-1)**, nunca para hoje ou depois. Ele é **idempotente**: a cada subida, preenche só os dias que faltam e que não têm dado real. Quando existem os dois para o mesmo período, **o real sempre vence** nas consultas. `uv_daily_summary.origin` indica a origem de cada dia, e a API devolve `contains_synthetic: true` nas respostas de histórico e comparação quando o período inclui dias sintéticos.

### 5.1 Banco de dados (proposta de tabelas)

| Tabela | Colunas principais | Observações |
|---|---|---|
| `city` | id, name, state, lat, lng, timezone, station_code | seed das 5 cidades; `station_code` único |
| `uv_reading` | id, city_id FK, measured_at (timestamptz), uv_index numeric(4,2), source (`openuv`/`simulado`), origin (`real`/`sintetico`), created_at | UNIQUE(city_id, measured_at, source); índice (city_id, measured_at desc); CHECK uv_index >= 0 |
| `uv_forecast_hourly` | id, city_id FK, forecast_for (timestamptz), uv_index, fetched_at, source | UNIQUE(city_id, forecast_for, source): upsert mantém a previsão mais recente |
| `uv_forecast_daily` | id, city_id FK, date, uv_max, weather_code, fetched_at, source | UNIQUE(city_id, date, source) |
| `uv_daily_summary` | city_id FK, date, uv_max, hours_above_8, origin | alimenta histórico e mapa de calor; recalculado a partir de `uv_reading` + seed |
| `alert` | id, client_id (uuid), city_id FK, threshold numeric, active bool, created_at | sem login: `client_id` gerado no navegador e guardado no localStorage |
| `alert_trigger` | id, alert_id FK, reading_id FK, triggered_at | gravado pelo coletor quando uma leitura passa do limite (no máximo 1 disparo por alerta por dia) |
| `skin_phototype` | code (I–VI) PK, description, med_j_m2, source | camada genética (seção 7) |
| `city_phototype_distribution` | city_id FK, phototype FK, share numeric, source, is_illustrative bool | camada genética (seção 7) |

As tabelas da genética entram numa migration própria, no fim, para poderem ser cortadas sem mexer no resto.

### 5.2 API REST (FastAPI, Swagger em `/docs`)

Prefixo `/api/v1`. Respostas em JSON, datas em ISO 8601 com fuso.

- `GET /health`: estado da API e do banco.
- `GET /cities`, com `?q=` para autocomplete.
- `GET /cities/nearest?lat=&lng=`: "usar minha localização".
- `GET /cities/{id}/current`: última leitura + nível OMS + recomendação + `stale` + `updated_at`.
- `GET /cities/{id}/today`: previsão horária 6h–19h, pico do dia, intervalos com UV ≤ 2.
- `GET /cities/{id}/forecast`: 5 dias.
- `GET /cities/{id}/history?period=7d|30d|12m`.
- `GET /compare?city_ids=1,2,3&date=`: tabela comparativa (atual, pico, horas acima de 8, tendência) + séries para o gráfico (até 4 cidades).
- `GET /compare/export.csv`: exportação CSV.
- `GET /map?when=now|peak_today|tomorrow`: todas as cidades com UV e coordenadas.
- `GET/POST/PATCH/DELETE /alerts` (filtradas por header `X-Client-Id`) e `GET /alerts/triggers`.
- (genética) `GET /phototypes` e `GET /cities/{id}/current?phototype=III`, que adiciona `minutes_to_burn`.
- `GET /readings?city_id=&from=&to=&page=`: consulta bruta paginada, para demonstrar o acesso remoto no README.

A classificação OMS (nível, cor, recomendação) é calculada **no backend**, num único módulo, e exposta na resposta. O front tem os tokens de cor, mas o nível vem da API. Assim a regra tem uma fonte só.

### 5.3 Testes

- Backend com pytest: classificação OMS (limites 2/3, 5/6, 7/8, 10/11), cálculo de pico e melhores horários, cálculo de minutos até queimar, provedores com HTTP mockado (incluindo a chave no header e os parâmetros na URL), endpoints principais contra um Postgres de teste (serviço no compose ou testcontainers, decisão do implementador).
- Front com Vitest: utilitários de escala e formatação. Testes de componente só onde forem baratos.
- GitHub Actions rodando lint + testes do backend. É um bônus: entra se sobrar tempo dentro do item 1.

## 6. Interface (briefing do Fernando, obrigatório)

O briefing completo está no Apêndice A. Pontos de implementação decididos:

- **Stack:** React + TypeScript + Vite + Tailwind CSS + Recharts + Leaflet (tiles OpenStreetMap). Componentes reutilizáveis `UvBadge`, `UvCard`, `UvTimeline`, `UvMap`, `CityCompareTable`. A escala OMS fica num único arquivo de tokens (`src/theme/uvScale.ts`).
- **Contraste:** as cores da escala devem ser ajustadas para o texto sobre elas ter contraste ≥ 4.5:1 (texto escuro sobre verde/amarelo/laranja e texto claro sobre vermelho/violeta, conforme o cálculo). Um teste Vitest verifica o contraste de cada par.
- **Busca de cidade:** autocomplete sobre as cidades cadastradas. "Usar minha localização" chama `/cities/nearest`.
- **Primeiro acesso:** pede a localização com uma frase de motivo. Se for negada, cai no seletor com São Paulo como padrão.
- **Noite:** se o UV atual for 0 e o horário for depois do pôr do sol, mostra mensagem amigável + pico previsto para amanhã.
- **Mapa, filtro de horário:** "agora" usa a leitura atual; "pico de hoje" e "amanhã" usam a previsão.
- **Alertas:** o disparo aparece como um aviso na própria interface (lista de disparos recentes na tela Alertas e um banner no Início se houver disparo hoje). Não há push.
- **Idioma da interface:** português do Brasil.

## 7. Camada genética (prioridade 5, pode ser cortada)

- **Fototipo de Fitzpatrick (I–VI):** na tela Início, uma linha opcional "Seu tipo de pele", com descrição leiga de cada tipo e escolha guardada no localStorage. Com o tipo escolhido, o card mostra "Você pode se queimar em cerca de N min agora".
- **Cálculo:** `minutos = MED / (UVI × 0,025 W/m²) / 60`, em que MED é a dose eritematosa mínima do fototipo em J/m². Os valores de MED por fototipo e a fonte (literatura de fotobiologia) ficam na tabela `skin_phototype` e no README. Com UV 0, não mostra o tempo.
- **Ponte com a genética:** o texto explicativo menciona que o fototipo tem forte componente genético (ex.: variantes do gene MC1R). É só informação contextual com fonte, sem coletar dado genético do usuário.
- **Comparar cidades:** coluna "Vulnerabilidade estimada" = UV de pico × proporção estimada da população com fototipos I–III. A distribuição por cidade é **ilustrativa** (`is_illustrative = true`) e rotulada assim na interface e no README.
- **Aviso fixo:** "Projeto demonstrativo. Não substitui orientação médica."

## 8. Git e entrega

- Repositório já iniciado em `GnTech/`, branch `main`.
- Commits pequenos no padrão Conventional Commits, em português, contando a história: estrutura → banco/migrations → coletor → API → Docker → front (por tela) → genética → README.
- O README em português traz: visão geral com diagrama, pré-requisitos, como obter a chave da OpenUV, `.env`, `docker compose up`, URLs (front, Swagger), exemplos de `curl` para consulta remota, coleção Postman exportada (opcional), modelagem das tabelas, decisões e trade-offs (limite da OpenUV, dados sintéticos, fontes científicas), como rodar os testes.
- O push para o GitHub acontece no fim, na conta do Fernando, depois de confirmação dele.
- **Acesso remoto (decisão do Fernando):** por enquanto, versão **local**. Isso significa a API REST acessível em `http://localhost:8000` após `docker compose up`, com Swagger e exemplos de `curl` no README. Publicar num servidor fica fora do escopo atual. A configuração por variáveis de ambiente (CORS, URLs) não deve impedir uma publicação futura.
- **Rastros de IA (decisão do Fernando):** os commits saem com a identidade do `git config` do Fernando e levam a linha `Co-Authored-By: Claude`. Este documento de design e o plano de implementação ficam versionados em `docs/`.

## 9. Deixado para o implementador

- Nomes internos de módulos e organização fina das pastas.
- Biblioteca de ícones, desenho exato dos skeletons e das animações (respeitando `prefers-reduced-motion`).
- Estratégia do banco de teste (serviço no compose ou testcontainers).
- Gerenciamento de estado e fetch no front (ex.: TanStack Query ou fetch simples).
- Ferramentas de lint/format (sugestão: ruff para Python, ESLint + Prettier para o front).

---

## Apêndice A: briefing de interface (texto do Fernando, na íntegra)

### Contexto
Crie a interface de um sistema de monitoramento da radiação ultravioleta (UV) em cidades. O sistema recebe leituras de estações/sensores espalhados por várias cidades, com o índice UV medido a cada [10 minutos], e também a previsão das próximas horas e dias.

O objetivo da interface é que qualquer pessoa entenda em até 5 segundos:
1. Qual é o nível de UV agora na cidade dela.
2. Se é perigoso e o que fazer (proteção).
3. Quando o UV vai subir ou cair hoje.

### Público
- Primário: cidadãos comuns, sem conhecimento técnico, muitas vezes pelo celular, ao ar livre e sob sol forte.
- Secundário: gestores de saúde pública e defesa civil, que comparam cidades e acompanham histórico.

### Princípios de design
- Simplicidade em primeiro lugar: um número grande, uma cor, uma frase. Detalhes só sob demanda.
- Hierarquia clara: o mais importante no topo e em maior destaque; o resto vem depois, de forma progressiva.
- Linguagem simples, sem jargão ("Muito alto: evite sol entre 10h e 16h", em vez de "IUV 9").
- Mobile-first, responsivo até o desktop.
- Alto contraste e boa leitura sob luz solar direta.
- Acessibilidade WCAG 2.1 AA: a cor nunca é a única forma de informar o nível (sempre há rótulo em texto e ícone), as áreas de toque têm no mínimo 44px e a navegação funciona pelo teclado e pelo leitor de tela.

### Escala de cores do índice UV (padrão OMS, obrigatória)
| Índice | Nível | Cor | Recomendação curta |
|---|---|---|---|
| 0–2 | Baixo | Verde | Sem proteção necessária |
| 3–5 | Moderado | Amarelo | Use protetor solar e óculos |
| 6–7 | Alto | Laranja | Protetor, chapéu, procure sombra |
| 8–10 | Muito alto | Vermelho | Evite sol entre 10h e 16h |
| 11+ | Extremo | Violeta | Evite exposição; proteção máxima |

Use essa escala de forma consistente em todos os componentes (cards, gráficos, mapa, alertas). O texto sobre cada cor deve manter contraste de no mínimo 4.5:1.

### Telas
**1. Início (cidade atual)**
- Seletor de cidade no topo (busca com autocomplete + "usar minha localização").
- Card principal: índice UV atual em número grande, nível por extenso, cor de fundo da escala, ícone e a recomendação em uma frase. Horário da última atualização ("atualizado há 4 min").
- Linha do tempo de hoje: gráfico de área ou barras por hora (6h–19h), com as faixas coloridas da escala ao fundo, marcador do "agora" e destaque do pico do dia ("Pico: 11 às 12h30").
- Faixa "Melhores horários para sair": intervalos com UV ≤ 2.
- Previsão de 5 dias: lista compacta com o UV máximo de cada dia, chip colorido e ícone do tempo.
- Bloco de dicas de proteção, conforme o nível atual (expansível).

**2. Mapa**
- Mapa das cidades/estações com marcadores coloridos pelo UV atual.
- Ao tocar em um marcador, abre um painel inferior (bottom sheet) com o resumo da cidade.
- Legenda fixa e discreta da escala.
- Filtro de horário (agora / pico de hoje / amanhã).

**3. Comparar cidades (painel para gestores)**
- Tabela ordenável: cidade, UV atual, pico do dia, horas acima de 8, tendência (seta + sparkline).
- Gráfico de linhas comparando até 4 cidades no mesmo dia.
- Histórico: seletor de período (7 dias / 30 dias / 12 meses) e mapa de calor do tipo calendário (dias × UV máximo).
- Exportar CSV.

**4. Alertas**
- O usuário escolhe as cidades e o limite ("me avise quando o UV passar de 8").
- Lista de alertas ativos, com interruptor para ligar e desligar cada um.

### Estados obrigatórios
- Carregando (skeleton, sem spinner em tela cheia).
- Sem dados / estação offline (mostrar o último valor válido, marcado como desatualizado).
- Noite (UV 0): mensagem amigável e a previsão do pico de amanhã.
- Erro de rede, com opção de tentar de novo.
- Primeiro acesso: pedir a localização, explicando o motivo em uma frase.

### Componentes visuais
- Tipografia sans-serif legível (ex.: Inter); número do UV entre 72 e 96px no mobile.
- Fundo neutro claro, com modo escuro opcional; a cor fica reservada para o nível de UV, para não competir.
- Gráficos limpos: sem grade pesada, eixos mínimos, tooltip ao tocar/passar o mouse, sem 3D.
- Navegação inferior no mobile (Início, Mapa, Comparar, Alertas); barra lateral no desktop.
- Animações sutis (transição de cor e de número), respeitando prefers-reduced-motion.

### Dados de exemplo
Use dados fictícios realistas para [São Paulo, Rio de Janeiro, Belo Horizonte, Curitiba, Fortaleza], com curva diária em sino (UV 0 de madrugada, pico entre 11h e 13h, chegando a 11–14 nas cidades do Nordeste).

Estrutura de cada leitura: `{ cidade, estacaoId, lat, lng, timestamp, uvIndex, previsao: [{ hora, uvIndex }] }`

### Stack (opcional)
[React + TypeScript + Tailwind CSS + Recharts + Leaflet], componentes reutilizáveis (UvBadge, UvCard, UvTimeline, UvMap, CityCompareTable) e a escala de cores em um único arquivo de tokens.

### Entregável
Interface navegável com as 4 telas, responsiva, preenchida com os dados de exemplo e com todos os estados listados. Priorize clareza em vez de quantidade de informação: se um elemento não ajuda o usuário a decidir "posso ficar no sol agora?", ele vai para um nível secundário.
