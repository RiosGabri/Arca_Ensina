---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: complete
completedAt: '2026-05-10'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/product-brief-Arca-Ensina.md
  - _bmad-output/planning-artifacts/product-brief-Arca-Ensina-distillate.md
  - docs/stories-v5.md
  - docs/README.md
  - docs/CONTRIBUTING.md
workflowType: 'architecture'
project_name: 'Arca-Ensina'
user_name: 'Euclides'
date: '2026-05-10'
---

# Architecture Decision Document — Arca-Ensina

_Este documento é construído colaborativamente, passo a passo. Seções são adicionadas conforme decisões arquiteturais são tomadas._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (47 FRs em 11 áreas):**

- **Identity & Access (FR1–5):** auth email/senha, JWT com refresh rotation, RBAC server-side de 4 perfis (`clinico`, `autor_clinico`, `pesquisador`, `admin`), rate limiting em endpoints de auth. Provisionamento admin-only.
- **Patient & Clinical Context (FR6–9):** cadastro de paciente como contexto persistente entre fluxos (peso, idade, sexo, sintomas em taxonomia estruturada); troca de paciente sem perder execuções em andamento.
- **Protocol Discovery (FR10–13):** sugestão automática por contexto, catálogo manual, busca por nome/sintoma/medicamento, modo emergência com protocolos pré-marcados.
- **Protocol Execution (FR14–19):** modo guiado (decision tree passo-a-passo com regras explícitas) + modo painel reativo (conversões de sedação Midazolam↔Diazepam, Morfina↔Metadona, Fentanil↔Morfina, Clonidina); calculadora integrada inline; timeline de decisões com versão exata do protocolo.
- **Safety-Critical Calculator (FR20–24):** dose por peso/idade/via, alerta visual de excesso, ajuste pediátrico automático, bulário digital com busca.
- **Offline & Sync (FR25–29):** operação completa após primeira sync; indicador de estado online/offline/sincronizando; fila persistente; LWW por timestamp; limpeza de PII após sync confirmado.
- **Clinical Authoring & Versioning (FR30–33):** versões imutáveis, diff entre versões, isolamento de execuções em andamento.
- **Audit, Privacy & Compliance (FR34–37):** AuditLog imutável de toda prescrição/decisão/acesso a dado sensível; consentimento granular separado clínico vs pesquisa; revogação retroativa só sobre coleta futura; disclaimer "ferramenta educacional".
- **Research Data (FR38–41):** modais opt-in pós-execução; painel agregado tabela+cards; filtros; export CSV anonimizado com hashes determinísticos.
- **Administration (FR42–44):** gestão de usuários e perfis, gestão da taxonomia de sintomas, inspeção de AuditLog.
- **Engagement (FR45–47):** dashboard pessoal, agenda de doses, notificações in-app.

**Non-Functional Requirements (drivers arquiteturais):**

- **Performance:** calculadora e painel com feedback ≤100ms (garantido por execução client-side); bundle de entrada ≤300KB gzip; sync ≤5s p95; busca ≤500ms.
- **Security:** HTTPS obrigatório, JWT acesso ≤15min com refresh rotation, hash PBKDF2, rate limiting (10/min login, 5/min refresh/register), permissões server-side em 100% das views, sem PII em logs, cookies `Secure`+`HttpOnly`+`SameSite=Lax`.
- **Reliability:** 100% das jornadas clínicas operam offline após primeira sync; retry com backoff sem perda silenciosa; idempotência por UUID; zero perda em ciclo offline→online demonstrada em E2E.
- **Data Integrity:** AuditLog e ProtocolVersion imutáveis (zero UPDATE/DELETE via API, com testes); paridade engine Python↔JS com zero divergência nos 9 tipos de passo; calculadora ≥95% cobertura + ≥50 edge cases; anonimização determinística.
- **Accessibility:** WCAG 2.1 AA em 100% das telas, Lighthouse a11y ≥90 em rotas críticas, navegação total por teclado, NVDA+VoiceOver, contraste ≥4.5:1, alvos ≥44×44px.
- **Compatibility:** evergreen (últimas 2 versões Chrome/Firefox/Safari/Edge; Safari iOS 15+); 3 breakpoints (≤640 / 641–1024 / ≥1025); IE fora.
- **Maintainability & Observability:** CI bloqueia em ESLint/TS strict/Prettier (FE) e ruff/black (BE); Conventional Commits via commitlint; README setup ≤30min; ≥5 ADRs obrigatórios; cobertura ≥80% global BE / ≥95% safety-critical / ≥70% FE; E2E nas 2 jornadas críticas; healthcheck `/api/v1/health/`.

**Scale & Complexity:**

- Primary domain: **full-stack web (SPA com meta PWA)** com domínio clínico safety-critical.
- Complexity level: **alta** — safety-critical + paridade dual-engine + versionamento imutável + LGPD operacional + WCAG AA + offline-first em 8 semanas.
- Estimated architectural components: **~12–15** (auth, accounts, protocols+versioning, protocol-engine python, protocol-engine js, panel-engine, calculator-engine, calculator-engine js, audit, consent/lgpd, research export, sync queue, patient context, taxonomy, notifications).

### Technical Constraints & Dependencies

- **Stack fixada (não-revisitar):** Django 6 + DRF + SimpleJWT + Python 3.12+; SQLite (dev) / PostgreSQL (prod); React 18 + TS + Vite 8; Node 20.19+ ou 22.12+; IndexedDB (provavelmente via `idb`); React Router; Docker Compose; GitHub Actions.
- **Brownfield com paralelismo:** codebase em `/home/euclides/Documentos/code/Arca_Ensina` com `apps/accounts`, `apps/audit`, `apps/protocols` e CORE-001 já entregues; endpoints `/api/v1/{auth,protocols,protocol-versions,audit,docs}/` existentes; CORE-002a/003/007 em desenvolvimento paralelo durante a definição da arquitetura.
- **Convenção forte (não-revisitar):** cada domínio = app Django próprio em `backend/apps/`; pasta por feature/domínio no FE (`src/features/<dominio>/`), não por tipo.
- **Pré-requisito não-negociável antes do Sprint 1:** workshop de 1 dia para modelar Dengue (`steps_data`) e Sedação (`panel_data`) em 2 fixtures JSON validados pelo autor clínico — define o schema declarativo concreto.
- **Stack do design system já decidida pela UX:** Tailwind CSS + Radix UI + shadcn/ui (componentes copiados, não dependência opaca); Storybook opcional.
- **Compliance:** LGPD operacional (não opcional); WCAG 2.1 AA como DoD; Lei 13.146/2015. Fora do escopo: ANVISA SaMD, CFM telemedicina, HIPAA/FDA/EU MDR (mitigado via disclaimer).
- **Restrições de equipe:** 11 pessoas semi-junior + 1 dev novo onboarding no Sprint 1 — favorece convenção sobre invenção, primitives consagrados sobre roll-your-own.

### Cross-Cutting Concerns Identified

1. **AuditLog transversal** — `AuditableMixin` aplicado a todos os models de domínio sensível; append-only enforced server-side; cobre prescrição, decisão clínica, acesso a dado sensível, e ações administrativas.
2. **Pipeline LGPD de privacidade** — middleware de anonimização determinística no export CSV; `ConsentLog` consultado em todo ponto de coleta de pesquisa; opt-out retroativo apenas sobre coleta futura; logs sem PII em texto.
3. **Versionamento imutável** — `ProtocolVersion` é referenciada por ID em toda execução; nova versão não muta antiga; isolamento de execuções em andamento; diff entre versões.
4. **Engine dual com paridade testada** — schema declarativo único como source of truth; suite de testes cross-platform compara saídas Python ↔ JS para os 9 tipos de passo do modo guiado; aplicável só ao modo guiado (painel é server-first com cache).
5. **Offline-first com sync determinística** — IndexedDB como cache + estado de execução; fila persistente com UUID client-side (idempotência); LWW por timestamp; engine de execução replicada client-side; calculadora client-side; banner de status; PWA install prompt como meta Sprint 3/4.
6. **RBAC server-side enforcement** — 4 perfis aplicados em 100% das views via Django permissions + DRF; jamais confiar em flag client-side; export de pesquisa exige perfil ≥ pesquisador + middleware de anonimização.
7. **Acessibilidade WCAG 2.1 AA como DoD transversal** — entregue majoritariamente via Radix primitives + tokens contrastados + linting de a11y; Lighthouse no CI; testes manuais Sprint 4.
8. **Disclaimer regulatório** — presente em UI (calculadora, painel, modo emergência), README, termo LGPD; reforça natureza educacional, mitiga risco de interpretação como SaMD.
9. **Observabilidade leve** — healthcheck endpoint, logs sem PII, error capture FE opcional (Sentry-like), AuditLog inspecionável.
10. **Documentação como entregável de primeira classe** — ≥5 ADRs obrigatórios, README setup ≤30min, CONTRIBUTING com Conventional Commits, guia de onboarding.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web: **Django 6 + DRF (backend)** + **React 18 SPA com Vite 8 (frontend)**, com meta de evolução para **PWA** nos Sprints 3/4. Stack **fixada pelo PRD** e não sujeita a revisão.

### Starter Options Considered

Em brownfield com scaffold já em produção paralela, starters genéricos foram avaliados apenas para descarte explícito:

- **Cookiecutter Django** — descartado: backend já tem `apps/accounts`, `apps/audit`, `apps/protocols` e SimpleJWT configurados; CORE-002a/003/007 em paralelo dependem desse esqueleto.
- **T3 / RedwoodJS / Blitz** — descartados: pressupõem TS end-to-end ou GraphQL/tRPC, incompatíveis com backend Django fixado.
- **Next.js / Remix** — descartados: PRD exclui SSR/SSG (produto 100% autenticado, sem requisito de SEO).
- **`create vite@latest` (react-ts)** — já aplicado na criação do frontend.

### Selected Starter: scaffold brownfield existente + adições controladas

**Rationale for Selection:**

O scaffold atual já carrega as decisões corretas para o domínio:
- Backend monorepo Django com convenção *cada domínio = app próprio* em `backend/apps/` (regra forte do projeto).
- `AuditableMixin` em `apps/audit` cobrindo o cross-cutting concern obrigatório (NFR-DI-1, FR34).
- `ProtocolVersion` imutável em `apps/protocols` (CORE-001 entregue, NFR-DI-2).
- Frontend Vite 8 + React 18 + TS strict, com convenção *pasta por feature/domínio* em `src/features/<dominio>/`.
- `/api/v1/{auth,protocols,protocol-versions,audit,docs}/` operacionais com Swagger.

Trocar o scaffold por starter genérico imporia retrabalho destrutivo durante desenvolvimento paralelo, sem ganho arquitetural — todas as decisões "que o starter teria feito" já estão tomadas e validadas.

**Initialization Command:**

Não-aplicável: brownfield. Setup local segue `docs/README.md` (reproduzido ≤30min conforme NFR-MAINT-3):

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend && npm ci && npm run dev

# Stack completa via Docker
docker compose up
```

### Architectural Decisions Already Provided by Existing Scaffold

**Language & Runtime:**
- Backend: Python 3.12+, Django 6, Django REST Framework, SimpleJWT, drf-spectacular (Swagger).
- Frontend: TypeScript strict, React 18, Vite 8, React Router. Node 20.19+ ou 22.12+.

**Styling Solution (per UX Spec):**
- Tailwind CSS como camada de tokens utilitários (paleta ARCA, tipografia, espaçamento, breakpoints).
- Radix UI como primitives acessíveis (Dialog, Combobox, Select, Tabs, Toast, Tooltip, Popover, AlertDialog).
- shadcn/ui como scaffold de componentes copiados ao repo (não dependência opaca de `node_modules`) — auditável em domínio safety-critical.

**Build Tooling:**
- Vite 8 com code-splitting por rota e lazy loading de módulos pesados (engine JS guiada, painel sedação).
- Bundle de entrada ≤300KB gzipped (NFR-PERF-2).

**Testing Framework:**
- Backend: `pytest` + `pytest-django` + `pytest-cov`; **`hypothesis`** (property-based) recomendado para os ≥50 edge cases da calculadora; `factory-boy` para fixtures clínicas; coverage ≥95% nos módulos safety-critical.
- Frontend: **Vitest** (unit) + **React Testing Library** (componente) + **Playwright** (E2E nas duas jornadas críticas: emergência guiada + offline-sync).
- Cross-platform: suite dedicada que compara saídas Python ↔ JS dos 9 tipos de passo do modo guiado (NFR-DI-3, zero divergência).

**Code Organization:**
- Backend: `backend/apps/<dominio>/` — cada domínio como app Django próprio (convenção forte).
- Frontend: `frontend/src/features/<dominio>/` — pasta por feature, espelhando a divisão do backend (`protocols`, `sedacao`, `calculator`, `patient`, `auth`, `audit`, `consent`, `research`, `bulario`, `taxonomy`, `notifications`, `dashboard`).

**Development Experience:**
- Linting/Formatting: ESLint + TS strict + Prettier (FE); `ruff` + `black` + `mypy strict` opcional (BE). CI bloqueia merge em falha (NFR-MAINT-1).
- Conventional Commits via `commitlint` em pre-commit (Husky + `lint-staged`); PR rejeitado pelo CI se commits fora do padrão (NFR-MAINT-2).
- Hot reload: `python manage.py runserver` (BE), `vite dev` (FE).

### Bibliotecas-chave a adicionar (versões atuais verificadas)

Adições ao scaffold para cumprir NFRs específicos do MVP. Cada uma deve virar decisão registrada em ADR ou nota arquitetural neste documento.

| Lib | Versão alvo | Domínio | Justificativa |
|---|---|---|---|
| `vite-plugin-pwa` + Workbox | `vite-plugin-pwa` ≥0.21 com `workbox-build`/`workbox-window` ^7.4 | Frontend | PWA Sprint 3/4 (manifest, SW, estratégias de cache, background sync). Suporte React first-class via `virtual:pwa-register/react`. |
| `idb` (Jake Archibald) | última estável | Frontend | Wrapper Promise-based sobre IndexedDB; cache de protocolos, fila de sync, paciente em sessão. |
| `@tanstack/react-query` | v5+ | Frontend | Server state + cache + retry/backoff; integra com SW para offline-first. |
| `react-hook-form` + `zod` | última estável | Frontend | Formulários validados (cadastro de paciente, login); schema Zod compartilhável com tipos. |
| `zustand` *ou* Context+reducers | — | Frontend | State management: decisão a fechar em ADR no Sprint 1 (PRD deixa em aberto); preferência por `zustand` pela simplicidade e bundle pequeno. |
| `dayjs` | última estável | Frontend | Datas leve para timeline e agenda de doses (alternativa a `date-fns`). |
| `django-ratelimit` *ou* DRF throttling | — | Backend | NFR-SEC-4 (rate limit em login/register/refresh). |
| `hypothesis` | última estável | Backend | Property-based testing para edge cases da calculadora (NFR-DI-4). |
| `factory-boy` + `pytest-factoryboy` | última estável | Backend | Fixtures clínicas para protocolos, paciente, prescrição. |
| `django-cors-headers` | última estável | Backend | CORS controlado para o frontend SPA. |
| `Sentry SDK` (opcional) | — | Full-stack | NFR-OBS-1 captura de erros FE; opcional no MVP. |

> **Nota:** versões exatas serão fixadas no momento da adição (Sprint 1 backend; Sprint 3 PWA), seguindo a política de "pin only com justificativa, senão deixar `^semver`".

**Note:** A inicialização do projeto não é uma story — está concluída. A primeira "story de fundação" ainda relevante é a adição do `vite-plugin-pwa` em **EXP-001a/Sprint 2** e a configuração do Workbox em **Sprint 3** dentro de EXP-001b/c.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (bloqueiam implementação) — todas decididas:**

- Tipo numérico para dose (`Decimal`).
- Validação de schema declarativo dual (`steps_data`/`panel_data`).
- Imutabilidade defensiva de `ProtocolVersion` e `AuditLog` (defesa em camadas).
- JWT storage no cliente (localStorage com mitigações).
- Idempotência de operações offline (UUID client-side em body).
- State management UI (Zustand) e server state (TanStack Query).
- Engine JS de protocolo (módulo paralelo ao Python com suite de paridade).
- Storage e retenção em IndexedDB (escopo de sessão + limpeza pós-sync).

**Important Decisions (moldam significativamente a arquitetura) — todas decididas:**

- Cache server-side (Django cache framework, sem Redis no MVP).
- Soft delete (`is_active=False`, sem soft-delete custom).
- Pagination strategy (page-number + cursor para AuditLog).
- Error contract (DRF default + `code` + `request_id`).
- Rate limiting (DRF throttling, sem `django-ratelimit`).
- Refresh rotation + blacklist (SimpleJWT defaults com `BLACKLIST_AFTER_ROTATION`).
- Encryption at rest (Postgres `pgcrypto` em colunas com PII direto).
- Disclaimer enforcement (componente `<EducationalDisclaimer />`, aceite registrado + rodapé fixo em rotas críticas).
- Forms (`react-hook-form` + `zod`).
- Code splitting (por rota + chunks dedicados para engine guiada e painel sedação).
- Hosting (VPS Linux com Docker Compose; Caddy como reverse proxy + Let's Encrypt).
- Postgres in-Compose (não managed).
- Static & media (WhiteNoise + Caddy servindo build do Vite).
- Logging (`structlog` JSON em prod, sem PII em texto).
- Deploy (GitHub Actions → SSH → `docker compose pull && up -d`).
- DB backup (`pg_dump` diário via cron, retenção 7 dias, documentado).
- Secrets (`.env` não-versionado, `.env.example` versionado).

**Deferred Decisions (registradas como open question / ADR pós-MVP):**

- **Manutenção do bulário pós-handoff** — quem versiona o seed clínico (Vinicius, ARCA Ensina, contribuição via PR) e por qual UI (Django admin no MVP). Não bloqueia o MVP — bulário roda com seed JSON inicial validado no workshop pré-Sprint-1.
- **Storybook** — opcional pelo PRD; descartado no MVP, reavaliar pós-MVP se design system crescer.
- **Sentry** — instrumentado como opt-in via env var (`SENTRY_DSN`); ativação fica como decisão operacional, não arquitetural.
- **Migração para CDN/managed Postgres** — fora do MVP; vetor para trajetória "produto comercial".
- **Dark mode / alto contraste opt-in** — UX flagrada como decisão a validar nos Sprints 3/4 com time clínico; tokens já em CSS variables para viabilizar.

### Data Architecture

- **Tipo numérico para dose:** `Decimal` em Python (`decimal.Decimal`, `DecimalField` com `max_digits=12, decimal_places=4` em models de medicamento/prescrição). No frontend, valores de cálculo manipulados como string + `Decimal.js` (ou conversão controlada para number só na renderização). **Justificativa:** float gera erros de arredondamento inaceitáveis em domínio safety-critical (NFR-DI-4). **Afeta:** CORE-003, CORE-004, CORE-005, PAINEL-001, PAINEL-002, EXP-002.
- **Validação de schema declarativo:** **JSONSchema** co-localizado em `backend/apps/protocols/schemas/{guided.schema.json, panel.schema.json}` e validado:
  - On-save no model (`ProtocolVersion.clean()`) usando `jsonschema` (Python).
  - On-render no frontend usando `ajv` (TS) — tipos derivados via `json-schema-to-typescript` em build.
  - Em testes (paridade engine): mesmas fixtures validadas pelos dois validadores.
  - **Justificativa:** schema declarativo é a fonte única da verdade da paridade dual-engine; JSONSchema é portável e ferramentas maduras existem dos dois lados.
- **Imutabilidade defensiva (`ProtocolVersion`, `AuditLog`):** três camadas:
  1. Model: `save()` com guard `if self.pk: raise ValidationError("Imutável")` para versões existentes; `AuditLog` sem método de update exposto.
  2. ViewSet DRF: apenas `list`/`retrieve`/`create` (sem `update`/`partial_update`/`destroy`).
  3. Testes de regressão que tentam `PATCH`/`DELETE` e verificam erro.
  - **Afeta:** CORE-001 ✅ (validar com check), `apps/audit`.
- **Caching server-side:** Django cache framework com `LocMemCache` em dev e backend `database` em prod (sem Redis no MVP). Cache de leitura para taxonomia de sintomas e listagem de protocolos (TTL 5min). **Justificativa:** carga prevista mínima, MVP single-region. Reavaliar pós-MVP se latência aparecer.
- **Soft delete:** apenas via `is_active=False` (Django default no modelo de usuário). Outros models (paciente, prescrição, execução) não têm soft-delete — manter histórico explícito é exigência clínica e LGPD respeita o princípio de minimização via janela de retenção, não delete.
- **Migrations:** padrão Django; squash apenas se >50 migrações em algum app; jamais reescrever histórico em `dev`/`main`. Brownfield: histórico já existe e deve ser preservado.
- **Bulário (FR23–24):** seed JSON inicial validado no workshop pré-Sprint-1, importado via `python manage.py loaddata`. Edição via Django admin (autor clínico). Manutenção pós-handoff em aberto.

### Authentication & Security

- **JWT storage no cliente:** **localStorage** para refresh + access tokens (decisão consciente para preservar setup atual SimpleJWT e velocidade do MVP).
  - **Mitigação obrigatória de XSS** (já que localStorage é vulnerável):
    - Content-Security-Policy estrito (`script-src 'self'`, sem `unsafe-inline`/`unsafe-eval`) — configurado via Caddy.
    - React escapa por default; **proibido `dangerouslySetInnerHTML`** salvo em conteúdo controlado e revisado em PR.
    - ESLint regra `react/no-danger` ativada como erro.
    - Sanitização de input clínico via Zod schema (sem permitir HTML/script em campos texto).
  - **Trade-off registrado:** se ARCA Ensina decidir trajetória comercial pós-MVP, migração para httpOnly cookie + CSRF é vetor de upgrade conhecido (registrar em ADR como "decisão revisitar").
- **Rate limiting:** DRF `AnonRateThrottle` + `UserRateThrottle` com escopos custom:
  - `LoginRateThrottle`: 10/min/IP.
  - `RegisterRateThrottle` / `RefreshRateThrottle`: 5/min/IP.
  - **Sem dependência adicional** (`django-ratelimit` descartado).
- **Refresh rotation + blacklist:** SimpleJWT `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`, `ACCESS_TOKEN_LIFETIME=15min`, `REFRESH_TOKEN_LIFETIME=7d`. App `rest_framework_simplejwt.token_blacklist` adicionado a `INSTALLED_APPS` com migração rodada.
- **Encryption at rest:** Postgres com `pgcrypto` extension em colunas com **PII direto** (nome do paciente, registro hospitalar). Outros campos clínicos (peso, idade, sintomas, prescrições) cleartext no DB — risco mitigado via HTTPS, RBAC server-side, AuditLog. **IndexedDB não criptografado**; defesa primária = escopo de sessão + limpeza após sync (FR29).
- **Disclaimer "ferramenta educacional":** componente `<EducationalDisclaimer />`:
  - Renderizado em onboarding pós-primeiro-login com aceite explícito; aceite gravado em `User.disclaimer_accepted_at` (timestamp).
  - Rodapé persistente em rotas safety-critical: calculadora (`/calculator/*`), painel sedação (`/sedation/*`), modo emergência (`/emergency/*`).
  - Texto auditado pelo cliente clínico antes do Sprint 4 (versionado em `frontend/src/locales/pt-BR/disclaimer.ts`).
- **HTTPS:** obrigatório em produção via Caddy + Let's Encrypt; redirect 301 de HTTP→HTTPS automático. Em dev: HTTP localhost OK.
- **CORS:** `django-cors-headers` com allowlist explícita ao domínio do frontend; `CORS_ALLOW_CREDENTIALS=False` (não usamos cookies cross-site).

### API & Communication Patterns

- **REST com versionamento de URL:** `/api/v1/...` (já em uso). Bump para `/v2/` apenas em breaking changes de schema; soft-deprecation com header `Deprecation` + `Sunset`.
- **OpenAPI:** `drf-spectacular` (já configurado em `/api/v1/docs/`). Tipos TypeScript do frontend gerados via `openapi-typescript-codegen` em script `npm run generate:api-types` (executado no CI).
- **Paginação:**
  - `PageNumberPagination` (default DRF) para listas curtas: protocolos, bulário, taxonomia, usuários.
  - `CursorPagination` para AuditLog e ProtocolExecution (séries temporais que crescem monotonicamente).
- **Error contract (extensão sobre DRF default):**
  ```json
  {
    "detail": "Mensagem human-readable em pt-BR",
    "code": "stable_machine_string",
    "request_id": "uuid-v4",
    "fields": { "campo_x": ["erro 1"] }   // opcional, para 400 de validação
  }
  ```
  Implementado via custom `EXCEPTION_HANDLER` no DRF. Frontend usa `code` para roteamento de UX (mensagem traduzida vem de `i18n` local).
- **Idempotência de mutations offline:**
  - Body inclui `client_uuid: <uuid v4>` em `POST /executions/`, `POST /prescriptions/`, `POST /research-responses/` etc.
  - DB constraint `UNIQUE(client_uuid)` por modelo; servidor responde 201 (criado) ou 200 (já existia, retorna o recurso existente).
  - Permite retry seguro pela fila de sync (NFR-REL-3).
- **Sync batch behavior:** **endpoints REST por recurso** (sem god-endpoint `/sync`). Service Worker dispara mutations em paralelo com limite (max 4 simultâneas) via `@tanstack/react-query` mutation queue.
- **Healthcheck:** `GET /api/v1/health/` retornando:
  ```json
  { "status": "ok", "version": "<git-sha>", "db_ok": true, "timestamp": "<iso8601>" }
  ```
  Sem auth. Usado em smoke tests do CI.

### Frontend Architecture

- **State management UI:** **Zustand** (~1KB). Stores por feature em `frontend/src/features/<dominio>/store.ts`. Padrão: store contém apenas estado UI/sessão (paciente em contexto, modal aberto, banner offline). Estado de dados de servidor fica no React Query.
- **Server state:** **`@tanstack/react-query` v5+** com:
  - `networkMode: 'offlineFirst'` global.
  - Mutations com `retry` exponencial + `onError` que enfileira no IndexedDB se offline.
  - `staleTime` específico por recurso (5min protocolos, 1h bulário, 0 healthcheck).
- **Forms:** `react-hook-form` v7+ + `zod` para validação. Schemas Zod em `frontend/src/features/<dominio>/schemas.ts`; tipos inferidos via `z.infer<>`.
- **Engine JS de protocolo (paridade Python ↔ JS):**
  - Localização: `frontend/src/engines/protocol/` espelhando estrutura de `backend/apps/protocols/engine/`.
  - **Suite de paridade:** `tests/parity/` com fixtures JSON compartilhadas (em `fixtures/protocols/`); cada fixture roda contra os dois engines e compara saída JSON normalizada (ordering-independent).
  - Engine **lazy-loaded** via `React.lazy` apenas na rota de execução guiada (NFR-PERF-2).
  - **Sem cálculo de dose dentro da engine** — engine produz "qual passo agora" + "qual cálculo aplicar"; calculadora é módulo separado em `frontend/src/engines/calculator/`.
- **Engine JS de calculadora:**
  - Localização: `frontend/src/engines/calculator/` espelhando `backend/apps/calculator/`.
  - Mesma suite de paridade que protocol engine.
  - 100% client-side em uso; servidor expõe endpoint `POST /api/v1/calculator/dose/` apenas para validação cruzada e fallback de testes.
- **IndexedDB / offline storage:**
  - Library: `idb` v8+ (wrapper Promise-based).
  - Localização: `frontend/src/lib/offline/` com DAOs explícitos:
    - `protocolCache.ts` — cache de protocolos + bulário (somente leitura, cache-first via SW).
    - `executionQueue.ts` — execuções e prescrições pendentes de sync.
    - `patientSession.ts` — paciente em contexto (apagado após sync confirmado, FR29).
  - Versionamento de schema explícito (`onupgradeneeded`) com migrations idempotentes.
  - Testes unitários com `fake-indexeddb`.
- **PWA (Sprint 3/4 stretch, fallback documentado):**
  - `vite-plugin-pwa` ≥0.21 com `workbox-build`/`workbox-window` ^7.4.
  - Estratégias: cache-first (assets), stale-while-revalidate (bulário), network-first com fallback offline (protocolos), network-only (auth), background-sync (mutations).
  - `useRegisterSW` hook do `virtual:pwa-register/react` para prompt de update.
  - Manifest com `display: standalone`, ícones 192/512/maskable, tema azul ARCA.
- **Routing & code splitting:**
  - React Router v6+ com lazy routes.
  - Chunks dedicados: `engines/protocol`, `engines/calculator`, `features/sedacao` (painel), `features/admin`.
  - Bundle de entrada (login + cadastro) ≤300KB gzipped (NFR-PERF-2).
- **Acessibilidade:**
  - Radix primitives entregam keyboard + ARIA + focus management por default.
  - ESLint plugin `eslint-plugin-jsx-a11y` no preset; CI bloqueia merge.
  - Lighthouse a11y check no CI nas rotas críticas (NFR-A11Y-2).

### Infrastructure & Deployment

- **Hosting:** VPS Linux genérico (Hetzner, DigitalOcean, AWS Lightsail, Linode — qualquer um serve; sem dependência específica). Recomendação prática para handoff: Hetzner CX22 (~€4/mês) ou DO Droplet Basic ($6/mês). Decisão final fica com ARCA Ensina.
- **Container orchestration:** Docker Compose (`docker-compose.yml` em `infra/`) com 4 serviços: `web` (Django + gunicorn), `db` (Postgres 16), `caddy` (reverse proxy + TLS), opcional `worker` (futuro, fora do MVP).
- **Reverse proxy:** Caddy 2 — HTTPS automático via Let's Encrypt, redirect HTTP→HTTPS, headers de segurança (HSTS, CSP, X-Content-Type-Options) por default.
- **Postgres:** container Postgres 16 in-Compose; volume nomeado para persistência. Backup operacional via `pg_dump` diário em cron no host, dump em volume separado, retenção 7 dias.
- **Static & media:** WhiteNoise para `/static/` (admin Django + ativos do DRF/Swagger); Caddy serve `frontend/dist/` (build Vite) como root.
- **Deploy pipeline (GitHub Actions):**
  - **`dev` branch:** lint + type-check + tests (BE+FE) + build → push imagem para registry (GHCR).
  - **`main` branch:** mesmo pipeline + deploy via SSH ao VPS (`docker compose pull web && docker compose up -d --no-deps web`).
  - Healthcheck pós-deploy: `curl /api/v1/health/` com retry; falha = rollback automático para imagem anterior.
- **Logging:** `structlog` no backend, JSON formatter em prod, key-value em dev. Configurado para nunca incluir PII (NFR-SEC-6) — processador custom remove campos `name`, `patient_name`, `email` por allowlist invertida.
- **Error capture:** Sentry **opt-in via `SENTRY_DSN` env var**; default desligado (NFR-OBS-1 marca como opcional). Sem custo se não ativado; trivial de ligar quando time decidir.
- **Observabilidade adicional:** Lighthouse CI roda no GitHub Actions em PRs tocando frontend; thresholds: a11y ≥90 (DoD), perf observado sem meta dura.
- **Secrets management:** `.env.example` versionado com placeholders; `.env` real **nunca** commitado (`.gitignore`). Em prod: `env_file: .env` no compose, com permissões `chmod 600` no host.
- **DNS & cert:** `caddy` cuida do cert automático; ARCA Ensina aponta subdomínio (ex.: `arca-ensina.example.org`) para o IP do VPS.

### Decision Impact Analysis

**Implementation Sequence (ordem que governa Sprint 1 → 4):**

1. Sprint 1 (em curso paralelo): JSONSchema dos protocolos + `Decimal` na calculadora + suite de testes paramétrica (CORE-003) + cadastro de paciente como contexto (CORE-007) + engine guiada Python (CORE-002a).
2. Sprint 1 (paralelo FE): tokens Tailwind ARCA + Radix primitives + shadcn copy + Zustand + React Query setup + `idb` DAOs base + ESLint a11y + Husky/commitlint.
3. Sprint 2: error contract DRF + paginations + endpoints idempotentes (`client_uuid`) + ConsentLog + middleware anonimização + `<EducationalDisclaimer />` + cache IndexedDB read-only (EXP-001a).
4. Sprint 3: engine JS guiada + suite de paridade + calculadora client-side + sync queue + Workbox + manifest PWA + painel sedação FE + export CSV.
5. Sprint 4: deploy pipeline GHA→VPS + Caddy config + `pg_dump` cron + Lighthouse CI thresholds + Sentry plumbing (opt-in) + ADRs finais + DPIA leve (stretch).

**Cross-Component Dependencies:**

- **Tipo `Decimal`** afeta calculadora, prescrição, painel sedação, export CSV (formatting consistente).
- **JSONSchema** afeta validação de model, admin do autor clínico, engine Python, engine JS, fixtures de teste e tipos TS.
- **Idempotência por `client_uuid`** afeta toda mutation offline-capable (execução, prescrição, research response, consent log).
- **Disclaimer aceite** bloqueia rotas safety-critical até gravado — afeta routing FE + state inicial pós-login.
- **AuditableMixin** já transversal; novas tabelas safety-critical (Prescription, Execution, Conversion) herdam por default.
- **Engine paridade** acopla CORE-002a (Python) ↔ EXP-001b (JS) ↔ suite cross-platform (precisa de fixtures comuns no repo).
- **CSP estrito** afeta tudo que carrega script externo — proibe inline scripts, então qualquer integração futura (Sentry, analytics) precisa via SDK npm com nonce ou self-hosted.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** ~30 áreas onde devs e agentes de IA poderiam tomar decisões divergentes, agrupadas em 6 categorias (naming, structure, format, communication, process, testing). Convenções abaixo **alinham com `docs/CONTRIBUTING.md`** já vigente; conflito = bug de PR review.

### Naming Patterns

**Database Naming (Django convention, snake_case):**
- Tabelas: `<app>_<model>` em snake_case plural natural (Django gera por default: `protocols_protocolversion`, `audit_auditlog`). **Não** sobrescrever `db_table` salvo motivo registrado em ADR.
- Colunas: `snake_case` (`patient_id`, `created_at`, `client_uuid`, `protocol_version_id`).
- Foreign keys: `<related_name>_id` (ex.: `protocol_version_id`, `user_id`). Nome do campo Django: sem `_id` (`patient = ForeignKey(...)`); o sufixo é só na coluna do banco.
- Indexes: deixar Django nomear (`<app>_<model>_<field>_<hash>`); explícito apenas se for composto e crítico para perf — então `idx_<app>_<descritivo>`.
- **Datas:** `created_at`, `updated_at`, `deleted_at` (se aplicável) — sempre TIMESTAMPTZ no Postgres, `auto_now_add` / `auto_now`.

**API Naming (REST + DRF):**
- Endpoints: **plural kebab-case** (`/api/v1/protocols/`, `/api/v1/protocol-versions/`, `/api/v1/research-responses/`). Já em uso ✓.
- Path params: `{id}` no OpenAPI; `<int:pk>`/`<uuid:client_uuid>` em `urls.py`. Sempre o nome canônico (`pk`, `client_uuid`), nunca `id` ambíguo.
- Query params: `snake_case` (`?from_date=2026-05-01&protocol_type=guiado`) para alinhar com payload JSON.
- Verbos REST padrão: `GET list/retrieve`, `POST create`, `PATCH partial_update`, `DELETE destroy`. **Custom actions** via `@action(detail=False/True)` com URL kebab-case (`/protocols/{id}/diff/`, `/protocol-versions/{id}/set-current/`).
- Headers customizados: prefixo `X-Arca-` (ex.: `X-Arca-Request-Id`).

**JSON field naming na API:** **snake_case** (alinhado ao Django). Frontend converte com helper `toCamelCase`/`toSnakeCase` em camada de transport (`frontend/src/lib/api/case.ts`); componentes consomem `camelCase`. **Não** misturar — bug recorrente em equipes mistas.

**Code Naming:**
- **Python:** `snake_case` para variáveis/funções/módulos, `PascalCase` para classes, `UPPER_SNAKE` para constantes. PEP-8 estrito (validado por `ruff`).
- **TypeScript:** `camelCase` para variáveis/funções, `PascalCase` para componentes/types/interfaces, `UPPER_SNAKE` para constantes module-level, `kebab-case` para nomes de arquivos **não-componente** (`api-client.ts`, `format-dose.ts`).
- **Componentes React:** `PascalCase.tsx` (`DoseCalculator.tsx`, `ProtocolStep.tsx`). Co-localizar `<Component>.test.tsx` e `<Component>.module.css` (se houver) na mesma pasta.
- **Hooks:** prefixo `use` (`useProtocolExecution`, `useOfflineQueue`).
- **Stores Zustand:** sufixo `Store` na variável e `use<Domain>Store` no hook (`usePatientStore`).
- **Schemas Zod:** sufixo `Schema` (`patientCreateSchema`, `prescriptionSchema`); tipos derivados sem sufixo (`PatientCreate = z.infer<typeof patientCreateSchema>`).
- **JSONSchema files:** `<domain>.schema.json` em `backend/apps/<domain>/schemas/`.

### Structure Patterns

**Project Organization (espelhamento BE↔FE):**

```
backend/
├── apps/
│   ├── accounts/        # já existe — auth + RBAC
│   ├── audit/           # já existe — AuditableMixin + AuditLog
│   ├── protocols/       # já existe — ProtocolVersion + engine
│   ├── calculator/      # CORE-003 (Sprint 1)
│   ├── patients/        # CORE-007 (Sprint 1)
│   ├── executions/      # CORE-002a (Sprint 1)
│   ├── sedation/        # PAINEL-001 (Sprint 2)
│   ├── bulario/         # CORE-005 (Sprint 2)
│   ├── consent/         # EXP-004 (Sprint 2) — ConsentLog + LGPD pipeline
│   ├── research/        # EXP-003, ADV-001, ADV-002
│   ├── taxonomy/        # FR43
│   └── notifications/   # ADV-004
├── project/             # settings, urls, base serializers
└── tests/parity/        # cross-engine Python↔JS parity suite

frontend/src/
├── features/
│   ├── auth/
│   ├── patient/
│   ├── protocols/
│   ├── sedacao/
│   ├── calculator/
│   ├── bulario/
│   ├── execution/
│   ├── consent/
│   ├── research/
│   ├── taxonomy/
│   ├── notifications/
│   └── dashboard/
├── engines/
│   ├── protocol/        # paridade com backend/apps/protocols/engine
│   └── calculator/      # paridade com backend/apps/calculator/engine
├── lib/
│   ├── api/             # client + transformers (snake↔camel)
│   ├── offline/         # idb DAOs (protocolCache, executionQueue, patientSession)
│   └── utils/
├── components/ui/       # shadcn copy (Button, Input, Dialog, Toast, ...)
├── locales/pt-BR/
└── routes/              # React Router config

fixtures/protocols/      # fixtures compartilhadas BE+FE+parity
```

**File-internal structure por feature (FE):**
```
features/<domain>/
├── api.ts               # mutation/query hooks (TanStack Query)
├── store.ts             # Zustand store (apenas estado UI/sessão)
├── schemas.ts           # Zod schemas
├── types.ts             # types não derivados de schema
├── components/          # UI da feature (PascalCase.tsx)
├── pages/               # rotas top-level (PascalCase.tsx)
├── hooks/               # use<Algo>.ts
└── index.ts             # barrel export controlado (apenas APIs públicas)
```

**File-internal structure por app (BE):**
```
apps/<domain>/
├── apps.py              # name = 'apps.<domain>'
├── models.py            # ou models/ se >1 model
├── serializers.py       # estende project.serializers.BaseSerializer
├── views.py             # ViewSets com AuditableMixin
├── permissions.py       # se houver permissions específicas
├── urls.py
├── schemas/             # JSONSchema files (se aplicável)
├── engine/              # se safety-critical (calculator, protocols, sedation)
├── fixtures/
├── migrations/
└── tests/
    ├── test_models.py
    ├── test_serializers.py
    ├── test_views.py
    └── test_engine.py   # se aplicável
```

**Tests location:**
- **BE:** `backend/apps/<domain>/tests/test_<unit>.py` (Django/pytest convention).
- **FE unit/component:** co-localizado `<Component>.test.tsx` ao lado do componente.
- **FE E2E:** `frontend/e2e/<jornada>.spec.ts` (Playwright).
- **Cross-engine parity:** `backend/tests/parity/test_<scenario>.py` carrega fixture compartilhada de `fixtures/protocols/` e roda Python; arquivo gêmeo em `frontend/tests/parity/<scenario>.test.ts` roda JS; suite final compara saídas via script CI.

**Shared utilities:**
- BE: `apps/<domain>/utils.py` se específico do domínio; `project/utils.py` se transversal.
- FE: `lib/utils/` para utilitários puros sem dependência de feature.
- **Proibido:** `helpers.ts`, `misc.ts`, `common.ts` — dump grounds que viram dívida.

### Format Patterns

**API response (DRF default + envelope mínimo de erro):**

Sucesso: `200/201` com **payload direto** (sem wrapper `{data: ...}`):
```json
{ "id": 42, "name": "Dengue Grave", "version": 3, "created_at": "2026-05-10T12:00:00Z" }
```

Listagem com paginação (DRF default):
```json
{ "count": 137, "next": "...", "previous": null, "results": [...] }
```

Erro (custom handler, alinhado ao type `ApiErrorResponse` já existente):
```json
{
  "detail": "Mensagem em pt-BR para humano.",
  "code": "stable_machine_string",
  "request_id": "uuid-v4",
  "fields": { "weight_kg": ["Deve ser positivo."] }
}
```

**Códigos `code` padronizados:** `validation_error`, `not_found`, `permission_denied`, `authentication_failed`, `rate_limited`, `idempotency_conflict`, `version_immutable`, `protocol_schema_invalid`, `consent_required`, `disclaimer_required`. Lista vive em `backend/project/error_codes.py` e em `frontend/src/lib/api/error-codes.ts` (manter sincronizado via teste de schema).

**Status codes uso:**
- `200 OK` — read sucesso, ou create idempotente que já existia.
- `201 Created` — create novo.
- `204 No Content` — delete (não usamos para audit/protocol; usamos para sessão/logout).
- `400 Bad Request` — validação ou payload mal-formado.
- `401 Unauthorized` — falta/inválido token.
- `403 Forbidden` — autenticado mas sem permissão.
- `404 Not Found` — recurso não existe ou usuário não pode vê-lo (não vazar existência).
- `409 Conflict` — versionamento/imutabilidade violado, idempotência conflitante.
- `422 Unprocessable Entity` — **NÃO usar** (DRF padrão é 400 para validação; manter consistência).
- `429 Too Many Requests` — rate limit.

**Data formats:**
- Datas: ISO 8601 com timezone (`2026-05-10T12:00:00-03:00` ou `Z`). Frontend converte para `dayjs` na borda.
- Booleans: `true`/`false` (nunca `1/0` ou `"yes"/"no"`).
- Null: explícito `null`, nunca string vazia para "ausente". Frontend trata `null` distinto de `""`.
- IDs: integer auto-increment para PKs server-side; `client_uuid` (UUID v4) para idempotência cross-side.
- Numéricos clínicos (peso, dose): **string decimal** na API (`"22.5"`), evita perda em float JSON. Frontend converte para `Decimal.js` na recepção.
- Arrays vs object para single item: array sempre que campo é semanticamente coleção, mesmo que vazia ou 1-element (`"symptoms": ["sangramento_mucoso"]`, nunca string solta).

### Communication Patterns

**State management (FE):**
- **Imutável sempre.** Zustand stores definidos com `set` que produz novo objeto (preferir spread; usar `immer` middleware apenas se profundidade ≥3 níveis).
- Nomes de actions: verbos claros (`setActivePatient`, `clearOfflineQueue`, `recordConsent`); **não** `handleX`/`onX` em store (esses ficam em componentes/hooks).
- Selectors: hooks dedicados (`const patient = usePatientStore(s => s.activePatient)`) para evitar re-renders desnecessários.
- **Proibido:** mutar estado retornado, fetch dentro de store (fetch vai em React Query mutation/query hooks em `features/<domain>/api.ts`).

**Server state (TanStack Query):**
- Query keys: array com hierarquia `[<domain>, <operation>, ...params]`. Ex.: `['protocols', 'list']`, `['protocols', 'detail', protocolId]`, `['executions', 'list', { patientId }]`. Manter padrão estrito — query invalidation depende disso.
- Mutations devolvem o recurso atualizado e fazem `queryClient.invalidateQueries` por chave hierárquica.
- Optimistic updates **apenas** em mutations idempotentes que afetam UI imediata (toggle de modal, marcar passo); **proibido** em mutations safety-critical (prescrição, decisão clínica) — esperar resposta do servidor.

**Eventos / hooks de Audit:**
- Backend: `AuditableMixin.create/update/destroy` registram automaticamente. Para eventos custom (acesso a dado sensível), chamar `audit.record(user, action, resource, ip, meta)` explicitamente.
- Action names: `<verb>.<resource>` em snake_case (`view.patient`, `create.prescription`, `export.research_csv`, `accept.disclaimer`).
- Payload: nunca PII bruto — IDs e hashes apenas (NFR-SEC-6).

**Logging:**
- BE via `structlog`: sempre log com chaves estruturadas, nunca f-string com dados.
  - ✅ `logger.info("execution.started", execution_id=ex.id, user_id=user.id)`
  - ❌ `logger.info(f"Execution {ex.id} started by {user.email}")` (vaza PII)
- Níveis:
  - `DEBUG` — apenas em dev, removido em prod por config.
  - `INFO` — eventos esperados (login OK, execução iniciada).
  - `WARNING` — situação recuperável (retry de sync, payload schema inválido).
  - `ERROR` — exceção tratada que merece atenção operacional.
  - `CRITICAL` — somente para falhas que afetam integridade clínica (ex.: divergência detectada em paridade engine em produção).
- FE: `console.error` apenas em desenvolvimento; em prod, vai para Sentry (se DSN configurado) e nunca contém PII.

### Process Patterns

**Error handling:**

**BE:**
- Sempre lançar exceção DRF (`ValidationError`, `NotFound`, `PermissionDenied`) com mensagem em **pt-BR**; jamais retornar `Response(status=400, ...)` manualmente (NFR + convenção CONTRIBUTING).
- Custom exceptions de domínio em `apps/<domain>/exceptions.py` herdando de `rest_framework.exceptions.APIException` com `default_code` correspondendo à lista padronizada.
- Custom `EXCEPTION_HANDLER` enriquece todas as respostas com `code` + `request_id`.

**FE:**
- ErrorBoundary global (`<AppErrorBoundary>`) em `App.tsx` — fallback minimalista com botão "recarregar"; nunca mostra stack trace ao usuário.
- ErrorBoundary por feature crítica (`<CalculatorErrorBoundary>`, `<ProtocolExecutionErrorBoundary>`) — fallback com instruções específicas e link para abrir bulário (último recurso clínico).
- `useMutation` `onError` traduz `data.code` para mensagem UX local via `lib/api/error-codes.ts`; nunca `data.detail` cru (esse é fallback).
- **Proibido:** `try/catch` swallow sem log + sem ação UX. Toda captura silenciosa precisa comentário `// engolido propositalmente porque ...`.

**Loading states:**
- Sempre 3 estados explícitos no UI: `idle/empty`, `loading`, `error`, `success`. **Não** assumir que ausência de erro = sucesso.
- TanStack Query expõe `isPending`, `isError`, `isSuccess` — usar diretamente.
- Skeleton loaders para listas (>200ms percebido); spinner apenas para ação inline (botão de submit). **Sem** spinner full-screen em fluxos clínicos.
- Estado offline: banner persistente no topo de toda rota autenticada (componente `<SyncStatusBanner />`); lê do `useOfflineStore`. Mensagens: `"Online — todas as decisões sincronizadas"` / `"Offline — N decisões salvas localmente, sincronizam ao reconectar"` / `"Sincronizando..."`.

**Retry & idempotência:**
- BE não retém estado de retry — confia em `client_uuid` para idempotência.
- FE: TanStack Query mutations com `retry: 3` e `retryDelay: exponentialBackoff(2000, 30000)` por default; **mutations safety-critical** (prescrição, painel de sedação) com `retry: 0` para evitar re-submissão acidental — usuário precisa retentar conscientemente.
- SW background sync: tenta indefinidamente até sucesso explícito com janela de backoff de até 1h.

**Authentication flow:**
- Login: `POST /api/v1/auth/login/` → `{access, refresh}` em localStorage.
- Access token expira em 15min: cliente intercepta 401, chama `POST /api/v1/auth/refresh/` automaticamente uma vez; se falhar, redireciona para login.
- Logout: `POST /api/v1/auth/logout/` (blacklist refresh) → limpar localStorage → limpar IndexedDB de paciente em sessão (FR29) → redirect.
- Auth header: `Authorization: Bearer <access_token>` em toda request autenticada (interceptor único em `lib/api/client.ts`).

**Validação (defesa em profundidade):**
1. **UI:** `react-hook-form` + Zod schema, validação onBlur/onSubmit.
2. **Transport:** Zod no client antes de enviar (mensagem em pt-BR para humano); JSONSchema no body de protocolos.
3. **API:** DRF `Serializer.validate()` rejeita o que passar; `ProtocolVersion.clean()` valida JSONSchema antes de salvar.
4. **DB:** constraints (`UNIQUE`, `NOT NULL`, `CHECK`) como rede final.

**Ordem é importante:** falhas devem aparecer no nível **mais alto possível** (UI mostra erro antes de submit). Mas testes precisam confirmar que **todos** os níveis rejeitam — UI burlada (curl direto) ainda é segura.

### Testing Patterns

**Pirâmide:**
- BE unit (models, serializers, engine puros, calculator) — maioria do volume; coverage ≥95% safety-critical.
- BE integration (views via DRF APIClient, com DB) — fluxo de cada endpoint.
- FE component (RTL) — comportamento de componentes interativos; coverage ≥70% global.
- FE E2E (Playwright) — apenas as 2 jornadas críticas (emergência guiada + offline-sync, NFR-MAINT-6).
- Parity (cross-engine) — BE+FE rodando mesma fixture; comparação determinística no CI.

**Naming de testes:**
- Python: `test_<comportamento_em_português>.py` opcional, mas funções `def test_<should_do_x_when_y>():` em inglês curto.
- TS: `describe('<Component>')` + `it('renders dose alert when above max')`.
- **Proibido:** `test_1`, `test_basic`, `test_works`. Nome do teste é a documentação.

**Fixtures:**
- BE: `factory-boy` em `apps/<domain>/factories.py`. Naming: `<Model>Factory` (ex.: `PatientFactory`, `PrescriptionFactory`).
- Protocolos seed: JSON em `fixtures/protocols/{dengue_guiado.json, sedacao_painel.json}` — única fonte para BE, FE, parity.
- Fixtures de calculadora (50+ edge cases): YAML em `apps/calculator/fixtures/edge_cases.yaml` carregado por teste paramétrico + `hypothesis` para varredura random.

### Enforcement Guidelines

**All AI Agents and Developers MUST:**

1. **Não duplicar `User`** — sempre `settings.AUTH_USER_MODEL` ou `get_user_model()` (regra forte do CONTRIBUTING).
2. **Não retornar `Response` de erro manualmente** — usar exceções DRF; o `EXCEPTION_HANDLER` enriquece (regra forte do CONTRIBUTING).
3. **Aplicar `AuditableMixin` antes de `ModelViewSet`** em todo recurso de domínio sensível.
4. **Cada domínio = um app Django próprio** — nunca misturar (regra forte).
5. **Nunca `dangerouslySetInnerHTML`** sem comentário justificando + revisão extra de PR.
6. **Idempotência via `client_uuid`** em toda mutation que pode ser reenviada (offline path).
7. **Conventional Commits com escopo** (`feat(core-007): cadastro de paciente`).
8. **Testes para cada novo endpoint** (≥1 happy path + ≥1 erro 400/403/404 conforme aplicável).
9. **Cobertura ≥95%** em código safety-critical (calculator, protocol engine, sedation engine); CI bloqueia merge se cair.
10. **Logs sem PII** — sempre IDs/hashes; CI tem grep de regressão para nomes de campos proibidos em logs (`patient_name`, `email`, `cpf`).
11. **JSONSchema validado em ambos os lados** quando alterar `steps_data` ou `panel_data`.
12. **Decimal para todo valor clínico**, nunca float.

**Pattern Enforcement:**

- **Automated:** ESLint, ruff, mypy (opcional), Prettier, commitlint, Lighthouse CI a11y, coverage threshold no CI, regex grep para PII em logs.
- **Manual:** code review com checklist (PR template em `.github/PULL_REQUEST_TEMPLATE.md`); Tech Lead em pair nos blocos safety-critical.
- **Violações documentadas:** issue com label `pattern-violation`; correção é P1.
- **Atualização de pattern:** PR alterando este documento + ADR específico em `docs/adr/`; aprovação Tech Lead obrigatória.

### Pattern Examples

**Good Examples:**

```python
# BE: ViewSet correto
class PrescriptionViewSet(AuditableMixin, viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsClinicoOrAuthor]

    def perform_create(self, serializer):
        serializer.save(prescriber=self.request.user)
```

```python
# BE: erro idiomático
from rest_framework import exceptions

if dose > max_dose:
    raise exceptions.ValidationError(
        {"dose_mg": ["Dose acima do máximo recomendado."]},
        code="dose_above_max",
    )
```

```typescript
// FE: query hook idiomático
export const useProtocols = () =>
  useQuery({
    queryKey: ['protocols', 'list'],
    queryFn: () => api.get<Protocol[]>('/protocols/'),
    staleTime: 5 * 60_000,
  });
```

```typescript
// FE: mutation idempotente
export const useCreatePrescription = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PrescriptionCreate) =>
      api.post('/prescriptions/', { ...input, client_uuid: crypto.randomUUID() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prescriptions'] }),
    retry: 0, // safety-critical: nunca re-submeter automaticamente
  });
};
```

**Anti-Patterns (proibidos):**

```python
# ❌ BE: erro retornado manualmente
return Response({'error': 'invalid'}, status=400)        # NÃO

# ❌ BE: float em dose
dose = weight_kg * mg_per_kg                              # NÃO — usar Decimal

# ❌ BE: import direto de User
from django.contrib.auth.models import User              # NÃO — usar get_user_model()
```

```typescript
// ❌ FE: error data renderizado cru
<p>{err.response.data.error}</p>                          // NÃO — é objeto

// ❌ FE: float em dose
const dose = weightKg * mgPerKg;                           // NÃO — usar Decimal.js

// ❌ FE: query key string solta
useQuery({ queryKey: 'protocols', ... });                  // NÃO — sempre array hierárquico
```

```python
# ❌ Logging com PII
logger.info(f"User {user.email} created prescription")    # NÃO — vaza PII
logger.info("prescription.created", user_id=user.id)      # ✅ correto
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
arca-ensina/
├── README.md                                # Setup ≤30min (NFR-MAINT-3) — já existe
├── CONTRIBUTING.md                          # Convenções de contribuição — já existe
├── LICENSE                                  # A definir (MIT recomendado para trajetória OSS pós-MVP)
├── .gitignore
├── .editorconfig                            # Convenções básicas (LF, UTF-8, indent)
├── .env.example                             # Template de env, sem segredos — já existe
├── docker-compose.yml                       # Stack completa (web + db + caddy) — já existe
├── docker-compose.dev.yml                   # Override dev (volumes, hot-reload)
├── docker-compose.prod.yml                  # Override prod (caddy, gunicorn)
├── Caddyfile                                # Reverse proxy + TLS (prod)
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                           # lint + test + build em PRs e dev
│   │   ├── deploy.yml                       # main → SSH ao VPS
│   │   ├── parity.yml                       # cross-engine Python ↔ JS
│   │   ├── lighthouse.yml                   # a11y + perf em PRs tocando FE
│   │   └── coverage.yml                     # threshold 80% global / 95% safety-critical
│   ├── PULL_REQUEST_TEMPLATE.md             # Checklist de pattern enforcement
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── pattern-violation.md
│   └── CODEOWNERS                           # Tech Lead em paths safety-critical
│
├── docs/
│   ├── README.md
│   ├── CONTRIBUTING.md                      # Espelho do raiz, opcional
│   ├── architecture.md                      # Este documento — fonte da verdade arquitetural
│   ├── adr/                                 # ≥5 ADRs (NFR-MAINT-4)
│   │   ├── 0001-engine-dual-python-js.md
│   │   ├── 0002-schema-declarativo-jsonschema.md
│   │   ├── 0003-versionamento-imutavel-protocolversion.md
│   │   ├── 0004-auditable-mixin-transversal.md
│   │   ├── 0005-pipeline-lgpd-anonimizacao.md
│   │   ├── 0006-jwt-localstorage-com-csp.md
│   │   ├── 0007-decimal-everywhere.md
│   │   ├── 0008-state-management-zustand.md
│   │   └── README.md                        # Índice + processo (template Nygard)
│   ├── lgpd-impact-assessment.md            # DPIA leve (stretch Sprint 4)
│   ├── operations.md                        # Deploy, backup, rollback, secrets
│   ├── onboarding.md                        # Guia novo dev (NFR-MAINT-3)
│   ├── api-error-codes.md                   # Lista canônica de `code` strings
│   └── stories-v5.md                        # Sprint plan — já existe
│
├── fixtures/                                # Compartilhadas BE+FE+parity
│   └── protocols/
│       ├── dengue_guiado.json               # Workshop pré-Sprint-1
│       ├── sedacao_painel.json              # Workshop pré-Sprint-1
│       └── README.md                        # Quem mantém, formato, validação
│
├── infra/
│   ├── caddy/
│   │   └── Caddyfile.prod                   # HTTPS + headers de segurança
│   ├── postgres/
│   │   └── init.sql                         # `CREATE EXTENSION pgcrypto;`
│   ├── scripts/
│   │   ├── backup-db.sh                     # pg_dump diário (cron no VPS)
│   │   └── restore-db.sh
│   └── github/
│       └── deploy-key-rotation.md           # SOP de rotação SSH
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml                       # ruff + black + mypy config
│   ├── requirements.txt                     # pinned production deps
│   ├── requirements-dev.txt                 # pytest, hypothesis, factory-boy
│   ├── manage.py
│   ├── conftest.py                          # pytest fixtures globais
│   ├── pytest.ini
│   │
│   ├── project/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                      # comum
│   │   │   ├── dev.py                       # SQLite, DEBUG
│   │   │   ├── prod.py                      # Postgres, CSP, HSTS
│   │   │   └── test.py
│   │   ├── urls.py                          # raiz, inclui /api/v1/
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   ├── serializers.py                   # BaseSerializer (já existe)
│   │   ├── permissions.py                   # IsClinico, IsAuthor, IsResearcher, IsAdmin
│   │   ├── pagination.py                    # PageNumber + Cursor presets
│   │   ├── exceptions.py                    # custom EXCEPTION_HANDLER
│   │   ├── error_codes.py                   # lista canônica `code` strings
│   │   ├── throttling.py                    # LoginRateThrottle, etc.
│   │   ├── logging.py                       # structlog + filtro PII
│   │   ├── middleware/
│   │   │   ├── audit_request.py             # request_id + ip
│   │   │   ├── csp.py                       # se Caddy não cobrir
│   │   │   └── anonymization.py             # pipeline LGPD para export
│   │   └── utils.py                         # determinístico hashing (LGPD)
│   │
│   ├── apps/
│   │   ├── accounts/                        # já existe (FR1–5, FR42)
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # User extendido com profile, disclaimer_accepted_at
│   │   │   ├── managers.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── permissions.py               # IsClinicoOrAuthor, IsAdmin etc.
│   │   │   ├── admin.py
│   │   │   ├── factories.py
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_models.py
│   │   │       ├── test_views.py
│   │   │       └── test_permissions.py
│   │   │
│   │   ├── audit/                           # já existe (FR34, NFR-DI-1)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # AuditLog (imutável)
│   │   │   ├── mixins.py                    # AuditableMixin
│   │   │   ├── recorder.py                  # audit.record(...)
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # admin-only inspection (FR44)
│   │   │   ├── urls.py
│   │   │   ├── filters.py                   # filtro por user/ação/período
│   │   │   ├── admin.py
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │
│   │   ├── protocols/                       # já existe (CORE-001 ✅)
│   │   │   ├── apps.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── protocol.py              # Protocol (catálogo)
│   │   │   │   └── protocol_version.py      # ProtocolVersion (imutável)
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # list/retrieve/diff/versions
│   │   │   ├── urls.py
│   │   │   ├── admin.py                     # autoria via admin (FR30–31)
│   │   │   ├── schemas/
│   │   │   │   ├── guided.schema.json       # `steps_data`
│   │   │   │   ├── panel.schema.json        # `panel_data`
│   │   │   │   └── README.md                # documenta os 9 tipos de passo
│   │   │   ├── engine/                      # CORE-002a (Sprint 1)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── interpreter.py           # interpreta steps_data
│   │   │   │   ├── step_types/              # 9 tipos: pergunta, calculo, etc.
│   │   │   │   ├── state.py                 # ExecutionState (snapshot)
│   │   │   │   └── exceptions.py
│   │   │   ├── factories.py
│   │   │   ├── fixtures/
│   │   │   │   ├── dengue_guiado.json       # → links para fixtures/ via gitignore?  NÃO: cópia explícita de teste
│   │   │   │   └── sedacao_painel.json
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_models.py
│   │   │       ├── test_immutability.py     # NFR-DI-2
│   │   │       ├── test_schema_validation.py
│   │   │       ├── test_engine_steps.py     # 9 tipos
│   │   │       └── test_views.py
│   │   │
│   │   ├── calculator/                      # CORE-003 (Sprint 1, safety-critical)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # Medication, Route, DoseFormula
│   │   │   ├── engine/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── compute.py               # Decimal-only
│   │   │   │   ├── adjustments.py           # ajuste pediátrico/peso/idade
│   │   │   │   ├── limits.py                # max dose checks
│   │   │   │   └── exceptions.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # POST /calculator/dose/
│   │   │   ├── urls.py
│   │   │   ├── factories.py
│   │   │   ├── fixtures/
│   │   │   │   ├── edge_cases.yaml          # 50+ cenários (NFR-DI-4)
│   │   │   │   └── medications_seed.json
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_compute.py          # cobre paramétricos básicos
│   │   │       ├── test_edge_cases.py       # 50+ via parametrize
│   │   │       ├── test_property.py         # hypothesis (decimal invariants)
│   │   │       └── test_views.py
│   │   │
│   │   ├── patients/                        # CORE-007 (Sprint 1, FR6–9)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # Patient (PII em pgcrypto)
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── factories.py
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │
│   │   ├── executions/                      # CORE-002a (Sprint 1, FR14–19)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # ProtocolExecution, ExecutionStep, Prescription
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # idempotência via client_uuid
│   │   │   ├── urls.py
│   │   │   ├── factories.py
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_idempotency.py
│   │   │       ├── test_version_pinning.py  # FR32: execução em andamento não migra
│   │   │       └── test_views.py
│   │   │
│   │   ├── sedation/                        # PAINEL-001 (Sprint 2, safety-critical)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # SedationConversion (matriz)
│   │   │   ├── engine/
│   │   │   │   ├── conversions.py           # 4 pares: Mid↔Diaz, Mor↔Met, Fent↔Mor, Cloni
│   │   │   │   ├── tapering.py              # tabela de desmame por dias
│   │   │   │   └── factors.py
│   │   │   ├── schemas/
│   │   │   │   └── panel.schema.json        # link semântico para protocols schema
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── factories.py
│   │   │   ├── fixtures/
│   │   │   │   └── conversions_seed.yaml
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_conversions.py      # cada par dedicadamente
│   │   │       ├── test_tapering.py
│   │   │       └── test_views.py
│   │   │
│   │   ├── bulario/                         # CORE-005 (Sprint 2, FR23–24)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # MedicationProfile, ActiveIngredient
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # search FR12 e FR24
│   │   │   ├── urls.py
│   │   │   ├── fixtures/
│   │   │   │   └── bulario_seed.json        # workshop pré-Sprint-1
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │
│   │   ├── consent/                         # EXP-004 (Sprint 2, FR35–36)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # ConsentLog (imutável append-only)
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_immutability.py
│   │   │       └── test_revocation.py       # opt-out retroativo apenas em coleta futura
│   │   │
│   │   ├── research/                        # EXP-003 + ADV-001 + ADV-002 (FR38–41)
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # ResearchResponse
│   │   │   ├── serializers.py
│   │   │   ├── views.py                     # painel + export CSV
│   │   │   ├── urls.py
│   │   │   ├── exporters.py                 # CSV anonimizado determinístico
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │       ├── test_export.py           # NFR-DI-5 anonimização determinística
│   │   │       └── test_consent_gate.py
│   │   │
│   │   ├── taxonomy/                        # FR7, FR43
│   │   │   ├── apps.py
│   │   │   ├── models.py                    # Symptom, SymptomCategory, Synonym
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py                     # gestão por admin
│   │   │   ├── fixtures/
│   │   │   │   └── taxonomy_seed.json
│   │   │   ├── migrations/
│   │   │   └── tests/
│   │   │
│   │   └── notifications/                   # ADV-004 (FR47), opcional descopável
│   │       ├── apps.py
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       ├── migrations/
│   │       └── tests/
│   │
│   └── tests/
│       ├── parity/                          # cross-engine Python ↔ JS
│       │   ├── README.md
│       │   ├── test_dengue_parity.py        # carrega fixtures/protocols/dengue_guiado.json
│       │   ├── test_calculator_parity.py
│       │   └── test_sedation_parity.py
│       └── e2e_seed/                        # seed completo para Playwright
│           └── fixtures.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts                       # com vite-plugin-pwa
│   ├── tailwind.config.ts                   # tokens ARCA
│   ├── postcss.config.js
│   ├── .eslintrc.cjs                        # + jsx-a11y + react/no-danger
│   ├── .prettierrc
│   ├── index.html
│   ├── public/
│   │   ├── icons/
│   │   │   ├── icon-192.png
│   │   │   ├── icon-512.png
│   │   │   └── icon-maskable.png
│   │   └── manifest.webmanifest             # gerado pelo plugin
│   │
│   ├── src/
│   │   ├── main.tsx                         # entrypoint, registra SW
│   │   ├── App.tsx                          # ErrorBoundary global, router
│   │   ├── routes.tsx                       # React Router config + lazy
│   │   ├── env.ts                           # validação de import.meta.env via Zod
│   │   │
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts                # axios/ky com interceptors
│   │   │   │   ├── case.ts                  # snake↔camel
│   │   │   │   ├── error-codes.ts           # mapping para mensagens UX
│   │   │   │   ├── refresh.ts               # auto-refresh JWT
│   │   │   │   └── types.ts                 # ApiErrorResponse já existente
│   │   │   ├── offline/
│   │   │   │   ├── db.ts                    # idb open + migrations
│   │   │   │   ├── protocolCache.ts
│   │   │   │   ├── executionQueue.ts
│   │   │   │   ├── patientSession.ts
│   │   │   │   ├── syncOrchestrator.ts      # processa fila ao reconectar
│   │   │   │   └── README.md
│   │   │   ├── auth/
│   │   │   │   ├── tokens.ts                # localStorage helpers
│   │   │   │   └── guard.tsx                # <RequireAuth> + <RequireRole>
│   │   │   ├── decimal.ts                   # wrapper de Decimal.js, NFR-DI-4
│   │   │   ├── format.ts                    # dose, peso, datas (dayjs)
│   │   │   └── pwa.ts                       # useRegisterSW wrapper
│   │   │
│   │   ├── engines/
│   │   │   ├── protocol/                    # EXP-001b (Sprint 3)
│   │   │   │   ├── interpreter.ts
│   │   │   │   ├── step-types/              # 9 tipos espelhando BE
│   │   │   │   ├── state.ts
│   │   │   │   ├── schema.ts                # Zod derivado de JSONSchema
│   │   │   │   └── README.md                # paridade — link para suite
│   │   │   └── calculator/                  # EXP-002 (Sprint 3)
│   │   │       ├── compute.ts               # Decimal.js
│   │   │       ├── adjustments.ts
│   │   │       ├── limits.ts
│   │   │       └── README.md
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                          # shadcn copy reskinned
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── alert-dialog.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   ├── tooltip.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── combobox.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   └── ...
│   │   │   └── shared/
│   │   │       ├── EducationalDisclaimer.tsx  # FR37
│   │   │       ├── SyncStatusBanner.tsx       # status online/offline
│   │   │       ├── EmergencyButton.tsx        # FAB persistente
│   │   │       ├── DoseFaixa.tsx              # barra de faixa terapêutica
│   │   │       ├── AuditTimelineItem.tsx
│   │   │       ├── AppErrorBoundary.tsx
│   │   │       └── PatientPill.tsx
│   │   │
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── api.ts
│   │   │   │   ├── store.ts                 # session state mínimo
│   │   │   │   ├── schemas.ts
│   │   │   │   ├── pages/
│   │   │   │   │   ├── LoginPage.tsx
│   │   │   │   │   └── DisclaimerOnboardingPage.tsx
│   │   │   │   └── components/
│   │   │   │
│   │   │   ├── patient/                     # CORE-007 FE
│   │   │   │   ├── api.ts
│   │   │   │   ├── store.ts                 # paciente em contexto
│   │   │   │   ├── schemas.ts
│   │   │   │   ├── pages/PatientCreatePage.tsx
│   │   │   │   └── components/SymptomChips.tsx  # taxonomia
│   │   │   │
│   │   │   ├── protocols/                   # CORE-002b, CORE-008, CORE-009
│   │   │   │   ├── api.ts
│   │   │   │   ├── store.ts
│   │   │   │   ├── pages/
│   │   │   │   │   ├── ProtocolCatalogPage.tsx
│   │   │   │   │   └── ProtocolExecutePage.tsx
│   │   │   │   ├── components/
│   │   │   │   │   ├── ProtocolStep.tsx
│   │   │   │   │   ├── SuggestionCard.tsx   # FR10 wow moment
│   │   │   │   │   └── ProtocolDiff.tsx
│   │   │   │   └── hooks/useProtocolExecution.ts
│   │   │   │
│   │   │   ├── sedacao/                     # PAINEL-002 (Sprint 3, safety-critical)
│   │   │   │   ├── api.ts
│   │   │   │   ├── store.ts
│   │   │   │   ├── pages/SedationPanelPage.tsx
│   │   │   │   └── components/
│   │   │   │       ├── ConversionMatrix.tsx
│   │   │   │       └── TaperingTable.tsx
│   │   │   │
│   │   │   ├── calculator/                  # CORE-004 (Sprint 2)
│   │   │   │   ├── api.ts
│   │   │   │   ├── pages/CalculatorPage.tsx
│   │   │   │   └── components/
│   │   │   │       ├── DoseInput.tsx
│   │   │   │       ├── DoseResult.tsx
│   │   │   │       └── DoseFaixaBar.tsx
│   │   │   │
│   │   │   ├── bulario/                     # CORE-005
│   │   │   ├── execution/                   # timeline auditável (FR16)
│   │   │   ├── consent/                     # EXP-004 modais opt-in
│   │   │   ├── research/                    # ADV-001/002 (perfil pesquisador)
│   │   │   ├── taxonomy/                    # admin
│   │   │   ├── notifications/               # ADV-004
│   │   │   ├── dashboard/                   # EXP-006
│   │   │   ├── emergency/                   # CORE-010
│   │   │   └── admin/                       # FR42–44 UIs admin
│   │   │
│   │   ├── locales/
│   │   │   └── pt-BR/
│   │   │       ├── common.ts
│   │   │       ├── disclaimer.ts            # texto auditado pelo cliente clínico
│   │   │       ├── errors.ts                # mapeamento de `code` → mensagem
│   │   │       └── domain.ts
│   │   │
│   │   ├── styles/
│   │   │   ├── tokens.css                   # CSS variables (alto contraste futuro)
│   │   │   └── globals.css
│   │   │
│   │   └── types/
│   │       ├── api.generated.ts             # gerado por openapi-typescript-codegen
│   │       └── domain.ts
│   │
│   ├── tests/
│   │   ├── parity/                          # gêmeo do BE
│   │   │   ├── dengue.test.ts
│   │   │   ├── calculator.test.ts
│   │   │   └── sedation.test.ts
│   │   ├── setup.ts                         # vitest + fake-indexeddb
│   │   └── helpers/
│   │
│   └── e2e/
│       ├── jornada1-emergencia.spec.ts      # Marina, Dengue
│       ├── jornada2-offline-sync.spec.ts    # Heitor, Midazolam→Diazepam
│       ├── fixtures/
│       └── playwright.config.ts
│
└── scripts/
    ├── generate-api-types.sh                # OpenAPI → frontend/src/types/
    ├── run-parity.sh                        # roda BE+FE parity localmente
    └── seed-dev.sh                          # carrega fixtures num DB limpo
```

### Architectural Boundaries

**API Boundaries (todas em `/api/v1/`):**

| Endpoint | App responsável | Permissão | Notas |
|---|---|---|---|
| `auth/{login,refresh,logout,register,user}/` | `accounts` | público / Auth | rate-limited (NFR-SEC-4) |
| `users/` | `accounts` | `IsAdmin` | FR42 |
| `patients/` | `patients` | `IsClinico` | PII em pgcrypto |
| `protocols/` + `/diff/`, `/versions/` | `protocols` | Auth | read-mostly, cache 5min |
| `protocol-versions/` + `/set-current/` | `protocols` | `IsAuthor` | imutável |
| `executions/` | `executions` | `IsClinico` | idempotência via `client_uuid` |
| `prescriptions/` | `executions` | `IsClinico` | safety-critical, retry: 0 |
| `calculator/dose/` | `calculator` | Auth | validação cruzada server-side |
| `bulario/` | `bulario` | Auth | search |
| `sedation/conversions/` | `sedation` | `IsClinico` | safety-critical |
| `consents/` | `consent` | Auth | imutável append-only |
| `research/responses/` | `research` | `IsClinico` (post) | opt-in via consentimento |
| `research/aggregate/` | `research` | `IsResearcher` | painel + filtros |
| `research/export.csv` | `research` | `IsResearcher` | middleware anonimização |
| `taxonomy/symptoms/` | `taxonomy` | Auth (read), `IsAdmin` (write) | FR7, FR43 |
| `audit/` | `audit` | `IsAdmin` | FR44, cursor pagination |
| `notifications/` | `notifications` | Auth | in-app |
| `health/` | `project.urls` | Public | NFR-OBS-3 |
| `docs/` | drf-spectacular | Public (dev) / Auth (prod) | Swagger UI |

**Component Boundaries (FE):**

- **Cross-feature communication = via React Query cache + Zustand stores compartilhados explícitos** (ex.: `usePatientStore` consumido por `protocols`, `calculator`, `sedacao`).
- **Proibido:** importar componentes de outra `features/<X>/` exceto via `index.ts` barrel; importar tipos é OK.
- **Componentes shared** ficam em `components/shared/` quando atendem ≥2 features; inicialmente vivem na feature originadora e migram quando segundo consumer aparece (regra: 2× = move).
- **Engine ↔ Feature:** features chamam engine via factory functions puras; engine **nunca** importa de feature.
- **Lib ↔ Feature:** features importam de `lib/`; `lib/` **nunca** importa de feature.

**Service Boundaries:**

- **Sem microsserviços** — monolito Django + SPA. Boundary é entre **app Django** e **feature React**, com contrato definido por OpenAPI.
- **Engine como pacote interno** com API pública estável (`run_step(state, input) -> next_state`) — backed-end e front-end importam o pacote, jamais reimplementam lógica.

**Data Boundaries:**

- **Postgres = source of truth** para tudo persistente.
- **IndexedDB = cache + estado de execução offline** com escopo de sessão (limpo no logout, FR29).
- **localStorage = apenas tokens JWT** (access + refresh).
- **In-memory only:** active patient (Zustand store, perdido em refresh — recarregado de IndexedDB se houver execução em andamento).
- **Schema migrations:**
  - DB: Django migrations, ordem imposta pelo grafo de dependências; sem reescrever histórico.
  - IndexedDB: versão incrementada em `db.ts`, migration handler idempotente em `onupgradeneeded`.

### Requirements to Structure Mapping

**Epic 1 — Fundamentos clínicos (Sprint 1):**
- CORE-001 ✅ `backend/apps/protocols/` (entregue)
- CORE-002a → `backend/apps/protocols/engine/` + `backend/apps/executions/`
- CORE-003 → `backend/apps/calculator/` (engine + tests + edge cases YAML)
- CORE-007 → `backend/apps/patients/` + `frontend/src/features/patient/`
- (FE paralelo) → `frontend/src/components/ui/` (shadcn copy) + `tailwind.config.ts` + tokens

**Epic 2 — Fluxo end-to-end + offline + coleta + painel BE (Sprint 2):**
- CORE-002b → `frontend/src/features/protocols/`, `frontend/src/features/execution/`
- CORE-004 → `frontend/src/features/calculator/`
- CORE-005 → `backend/apps/bulario/` + `frontend/src/features/bulario/`
- CORE-009 → `frontend/src/features/protocols/pages/ProtocolCatalogPage.tsx`
- EXP-001a → `frontend/src/lib/offline/protocolCache.ts` + integração com React Query
- EXP-003 → `backend/apps/research/` + `frontend/src/features/consent/`
- EXP-004 → `backend/apps/consent/` + `frontend/src/features/consent/`
- PAINEL-001 → `backend/apps/sedation/` (engine)

**Epic 3 — Inteligência + offline + painel FE (Sprint 3):**
- CORE-008 → `frontend/src/features/protocols/components/SuggestionCard.tsx` + endpoint sugestão
- CORE-010 → `frontend/src/features/emergency/` + `frontend/src/components/shared/EmergencyButton.tsx`
- PAINEL-002 → `frontend/src/features/sedacao/` (safety-critical FE)
- EXP-001b → `frontend/src/engines/protocol/` + `frontend/tests/parity/`
- EXP-001c → `frontend/src/lib/offline/syncOrchestrator.ts` + `executionQueue.ts`
- EXP-002 → `frontend/src/engines/calculator/`
- ADV-001 → `frontend/src/features/research/`
- ADV-002 → `backend/apps/research/exporters.py` (CSV anonimizado)
- ADV-004 → `backend/apps/notifications/` + `frontend/src/features/notifications/`

**Sprint 4 — Polimento + handoff:**
- EXP-006 → `frontend/src/features/dashboard/`
- ADV-006 → cross-cutting perf (vite-plugin-pwa hardening, code-splitting tuning)
- ADV-007 → `frontend/e2e/`, `docs/adr/`, `docs/onboarding.md`, `README.md` final
- PAINEL-003 → `backend/apps/notifications/` + `frontend/src/features/dashboard/` (agenda)
- (Stretch) DPIA → `docs/lgpd-impact-assessment.md`
- (Stretch) PWA completo → `frontend/vite.config.ts` + `public/manifest.webmanifest`

**Cross-Cutting Concerns:**
- AuditLog → `backend/apps/audit/` + `AuditableMixin` aplicado em todos os ViewSets sensíveis
- LGPD pipeline → `backend/project/middleware/anonymization.py` + `backend/apps/consent/` + `backend/apps/research/exporters.py`
- Disclaimer → `frontend/src/components/shared/EducationalDisclaimer.tsx` + `frontend/src/features/auth/pages/DisclaimerOnboardingPage.tsx` + `User.disclaimer_accepted_at`
- A11y → ESLint `jsx-a11y` + Lighthouse CI workflow + Radix primitives default
- Idempotência → `client_uuid` em mutations (`executions`, `prescriptions`, `consents`, `research-responses`)
- Paridade engine → `backend/tests/parity/` + `frontend/tests/parity/` + `fixtures/protocols/` + `.github/workflows/parity.yml`

### Integration Points

**Internal Communication (FE ↔ BE):**
- HTTP REST com JSON via `lib/api/client.ts` (axios ou ky com interceptors).
- Auto-refresh JWT em interceptor de response 401.
- Erros padronizados com `code` machine-string + tradução local em `locales/pt-BR/errors.ts`.

**Internal Communication (FE ↔ FE):**
- React Query cache + queryKey hierárquico para invalidation.
- Zustand stores publicados em `features/<X>/store.ts`; subscriptions via hooks.
- Service Worker postMessage para coordenar background-sync com tabs abertas.

**Internal Communication (BE ↔ BE):**
- Django signals para AuditLog hooks (criação/edição em models AuditableMixin).
- `audit.record(...)` chamado explicitamente em operações sem ViewSet (ex.: `accept.disclaimer`).
- Middleware enriquece request com `request_id` (UUID) propagado em logs e em `error.request_id`.

**External Integrations:**
- **Nenhuma obrigatória no MVP** (sistema autocontido).
- **Opcional:** Sentry (HTTP-only DSN, sem PII). Plug-and-play.
- **Pós-MVP** (registrar como vetor): EHR via FHIR/HL7, TUSS/CID-10, SSO institucional.

**Data Flow (acende o sistema):**

1. **Cadastro de paciente (online):** UI → `react-hook-form` valida → `lib/api/client` envia `POST /patients/` → Django serializer valida + cria → `AuditableMixin` registra → response → React Query cache → Zustand `patientStore.activePatient` atualizado.
2. **Cadastro offline:** mesmo fluxo até `lib/api/client`; interceptor detecta offline → adiciona à `executionQueue` no IndexedDB com `client_uuid` → SW background-sync dispara ao reconectar → idempotência server-side garante zero duplicação.
3. **Execução guiada offline:** engine JS interpreta `steps_data` localmente → cada passo gera evento na timeline (state local + IndexedDB) → fila de sync drena ao reconectar → server reconcilia via `client_uuid`.
4. **Painel sedação:** input no FE → engine local calcula tabela de desmame em <100ms → usuário prescreve → `POST /sedation/conversions/` (+ `Prescription`) com `client_uuid` → AuditLog.
5. **Export pesquisa:** Researcher hits `/research/export.csv` → middleware aplica anonimização determinística (hash com salt fixo no settings) → resposta streaming CSV.

### File Organization Patterns

**Configuration Files:**
- Raiz: `docker-compose.yml`, `.env.example`, `Caddyfile`, `.gitignore`, `.editorconfig`.
- Backend: `pyproject.toml`, `requirements*.txt`, `pytest.ini`, `manage.py`, `conftest.py`.
- Frontend: `package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.ts`, `.eslintrc.cjs`, `.prettierrc`.
- Settings Django: `backend/project/settings/{base,dev,prod,test}.py`.
- Env: `.env.example` versionado (placeholders); `.env` real `.gitignore`'d.

**Source Organization:**
- Espelho BE↔FE por domínio (`apps/<X>/` ↔ `features/<X>/`).
- Engines em pacote separado (`engines/<X>/`) — não pertencem a uma feature, são consumidos por elas.
- `lib/` para infra do FE (api client, offline, auth helpers); `project/` para infra do BE (settings, middleware, base classes).

**Test Organization:**
- Co-localização (`apps/<X>/tests/` BE; `<Component>.test.tsx` FE) — fácil descobrir testes, atualizar junto.
- Suíte de paridade dedicada (`tests/parity/` em ambos os lados) — não vive em domínio, é cross-cutting.
- E2E isolado em `frontend/e2e/` — só 2 jornadas críticas no MVP.

**Asset Organization:**
- Estáticos do FE em `frontend/public/` (ícones PWA, manifest).
- Build output do FE em `frontend/dist/` (servido pelo Caddy, gitignore'd).
- Static do Django (admin, DRF) servido por WhiteNoise.

### Development Workflow Integration

**Development Server Structure:**
- `docker compose up` (com override `dev.yml`): Django runserver :8000 + Vite :5173 + Postgres (ou SQLite via volume).
- Manual: `python manage.py runserver` + `npm run dev` em terminais separados.
- Vite proxy: `/api/...` → `localhost:8000`.

**Build Process Structure:**
- BE: `python manage.py collectstatic --noinput` + `gunicorn` (em prod, dentro do container).
- FE: `npm run build` → `frontend/dist/` com chunks code-split por rota + chunks de engine.
- Imagens Docker buildadas pelo CI a cada push em `main` ou tag.
- OpenAPI types gerados em `npm run generate:api-types` (executado no CI antes de `npm run build`).

**Deployment Structure:**
- GitHub Actions push para registry GHCR (imagens `arca-ensina-backend:<sha>`, `arca-ensina-frontend:<sha>`).
- Deploy SSH ao VPS: `docker compose -f docker-compose.prod.yml pull && up -d --no-deps`.
- Caddy serve `frontend/dist/` via volume; backend exposto em `:8000` interno; HTTPS auto via Let's Encrypt.
- Healthcheck pós-deploy: retry 5x com 5s; falha = `docker compose rollback` para tag anterior.
- Backup `pg_dump` em cron host, retenção 7 dias em volume `/var/backups/arca-ensina/`.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Stack pinada (Django 6 + DRF + SimpleJWT + Postgres + React 18 + Vite 8 + TS) é compatível e em produção brownfield. Versões verificadas: Python 3.12+, Node 20.19+/22.12+, vite-plugin-pwa ≥0.21 com Workbox ^7.4.
- Decisões de cliente (`Decimal.js`, `idb`, `@tanstack/react-query`, `react-hook-form`+`zod`, Zustand) compõem stack reconhecida sem dependências circulares ou conflitos de bundler.
- JWT em localStorage + SimpleJWT é compatível; CSP estrito + `react/no-danger` mitigam o XSS surface aceito conscientemente.
- Engine dual (Python + JS) com schema declarativo único (JSONSchema) elimina divergência por construção; a suite de paridade fecha o loop com teste cross-platform automático.

**Pattern Consistency:**
- Convenções de naming alinham com `docs/CONTRIBUTING.md` brownfield (snake_case BE, camelCase FE com transformer, kebab-case URLs, Conventional Commits com escopo).
- Cross-cutting concerns têm dono único e localização canônica: AuditLog em `apps/audit`, ConsentLog em `apps/consent`, anonimização em `project/middleware/anonymization.py`, AppErrorBoundary em `components/shared/`.
- Padrão de erros (`code` + `request_id` + `fields`) é uniforme do `EXCEPTION_HANDLER` ao mapping em `lib/api/error-codes.ts`; erros DRF jamais usam `Response` manual (regra forte do CONTRIBUTING).

**Structure Alignment:**
- Espelhamento BE↔FE por domínio (`apps/<X>/` ↔ `features/<X>/`) torna ownership e impacto de mudança previsível.
- Engines isolados em `engines/<X>/` (não em features) refletem corretamente o fato de que são consumidos por múltiplas features e têm semântica de paridade cross-platform.
- Boundaries respeitam acoplamento: `lib/` ↛ feature, engine ↛ feature, cross-feature via barrel apenas — regras passíveis de validação automática (ESLint `no-restricted-imports`).

### Requirements Coverage Validation

**Functional Requirements (47/47 cobertos):**

| FR área | Cobertura arquitetural |
|---|---|
| FR1–5 Identity & Access | `apps/accounts` ✅ + DRF throttling + SimpleJWT rotation/blacklist |
| FR6–9 Patient Context | `apps/patients` + `frontend/src/features/patient` + Zustand `patientStore` |
| FR10–13 Protocol Discovery | `apps/protocols` + endpoint sugestão (CORE-008) + `features/protocols/components/SuggestionCard.tsx` + `features/emergency` |
| FR14–19 Protocol Execution | `apps/protocols/engine` + `apps/executions` + `engines/protocol` (JS) + `apps/sedation` + `features/sedacao` |
| FR20–24 Calculator + Bulário | `apps/calculator` (engine + edge cases YAML) + `apps/bulario` + `engines/calculator` (JS) |
| FR25–29 Offline & Sync | `lib/offline/{db,protocolCache,executionQueue,patientSession,syncOrchestrator}` + Workbox + `client_uuid` idempotência |
| FR30–33 Authoring & Versioning | `ProtocolVersion` imutável (3 camadas de defesa) + Django admin + endpoint `/diff/` |
| FR34–37 Audit/Privacy/Disclaimer | `AuditableMixin` + `apps/consent` (ConsentLog imutável) + `<EducationalDisclaimer/>` com aceite registrado |
| FR38–41 Research Data | `apps/research` + `features/research` + middleware anonimização + export CSV determinístico |
| FR42–44 Administration | `apps/accounts` (FR42) + `apps/taxonomy` (FR43) + `apps/audit/views` admin-only (FR44) |
| FR45–47 Engagement | `features/dashboard` + `apps/notifications` + agenda em `apps/sedation`/PAINEL-003 |

**Non-Functional Requirements (29/29 endereçados):**

| NFR | Onde está coberto |
|---|---|
| NFR-PERF-1 (≤100ms calc/painel) | Cálculo client-side via `engines/{calculator,protocol}` |
| NFR-PERF-2 (≤300KB gzip entrada) | Code-splitting Vite por rota + chunks dedicados |
| NFR-PERF-3 (sync ≤5s p95) | TanStack Query com `networkMode: offlineFirst` + Workbox background sync |
| NFR-PERF-4 (busca ≤500ms) | Postgres ILIKE em datasets MVP (≤100 medicamentos, ≤10 protocolos); cache 5min em catálogo |
| NFR-PERF-5 (Web Vitals best effort) | `lighthouse.yml` workflow no CI |
| NFR-SEC-1 (HTTPS obrigatório) | Caddy + Let's Encrypt |
| NFR-SEC-2 (PBKDF2) | Django default |
| NFR-SEC-3 (JWT 15min + refresh rotation) | SimpleJWT settings |
| NFR-SEC-4 (rate limit) | DRF throttling em `project/throttling.py` |
| NFR-SEC-5 (RBAC server-side 100%) | `project/permissions.py` + `apps/accounts/permissions.py` em todo ViewSet |
| NFR-SEC-6 (logs sem PII) | `structlog` filter custom em `project/logging.py` + grep CI |
| NFR-SEC-7 (export anonimização) | `project/middleware/anonymization.py` + `apps/research/exporters.py` |
| NFR-SEC-8 (cookies Secure/HttpOnly) | N/A no MVP — JWT em localStorage; convenção registrada para uso futuro de cookies |
| NFR-REL-1 (100% jornadas offline) | Engines locais + IndexedDB + Workbox |
| NFR-REL-2 (retry com backoff) | TanStack Query + Workbox background sync |
| NFR-REL-3 (idempotência UUID) | `client_uuid` em mutations + DB constraint UNIQUE |
| NFR-REL-4 (zero perda) | E2E offline-sync (`jornada2-offline-sync.spec.ts`) |
| NFR-REL-5 (zero sev-1) | Backlog herdado documentado |
| NFR-DI-1 (AuditLog imutável) | Defesa em 3 camadas + teste de regressão |
| NFR-DI-2 (ProtocolVersion imutável) | Defesa em 3 camadas + teste de regressão |
| NFR-DI-3 (paridade engine) | Suite `tests/parity/` BE+FE com fixtures comuns |
| NFR-DI-4 (calculadora ≥95% + 50 edge) | `apps/calculator/fixtures/edge_cases.yaml` + `hypothesis` + threshold no CI |
| NFR-DI-5 (anonimização determinística) | Hash com salt fixo em settings; teste em `apps/research/tests/test_export.py` |
| NFR-A11Y-1..7 | Radix primitives + Tailwind tokens contrastados + `eslint-plugin-jsx-a11y` + Lighthouse CI ≥90 |
| NFR-COMP-1..4 | Vite alvos + 3 breakpoints Tailwind + browserslist evergreen |
| NFR-MAINT-1..6 | CI workflows (lint/test/coverage) + commitlint + ADRs em `docs/adr/` + Playwright E2E |
| NFR-OBS-1..3 | Sentry opt-in + `/api/v1/health/` + AuditLog filtrável |

**Cross-Epic Dependencies (do `stories-v5.md`):**
- CORE-001 → CORE-002a → CORE-002b ✅ caminho coberto
- CORE-003 → CORE-004 → EXP-002 ✅ engine + UI + offline
- PAINEL-001 → PAINEL-002 → PAINEL-003 ✅
- EXP-001a → EXP-001b → EXP-001c → ADV-007 ✅ offline pipeline + E2E

### Implementation Readiness Validation

**Decision Completeness:** todas as decisões críticas têm versão (quando aplicável) e justificativa documentada; nenhuma decisão crítica está em aberto.

**Structure Completeness:** árvore enumera ~250 entradas com responsabilidade clara; cada story de cada sprint mapeia para diretório concreto.

**Pattern Completeness:** 6 categorias de padrões (naming, structure, format, communication, process, testing) com 12 regras MUST + exemplos bons/anti-patterns; ESLint/ruff/commitlint/coverage threshold cobrem enforcement automático.

### Gap Analysis Results

**Critical Gaps:** _nenhum identificado_. Todos os FRs/NFRs têm cobertura arquitetural; nenhuma decisão crítica está em aberto que bloqueie Sprint 1.

**Important Gaps (não bloqueiam, mas valem nota):**

1. **Algoritmo de sugestão automática (CORE-008, FR10):** arquitetura provê o endpoint e o componente, mas o **algoritmo de matching sintoma↔protocolo** não está formalizado — match-count simples? Pesos por sintoma definidos no `Protocol.metadata`? Decisão a fechar no início do Sprint 3 com input do autor clínico. **Mitigação:** registrar como ADR-0009 quando definido; não bloqueia; default razoável é match-count com tie-break por ordem de catálogo.
2. **Versionamento do disclaimer:** se o texto do disclaimer for atualizado pós-aceite inicial, usuários atuais devem re-aceitar? Não modelado. **Recomendação:** adicionar `User.disclaimer_version_accepted` (int) e comparar com `DISCLAIMER_VERSION` no settings; força re-aceite ao bumpar versão. Item para ADR + 1 migração quando texto for finalizado.
3. **LGPD vs backups:** se um usuário/paciente exercer direito de supressão (LGPD art. 18), os 7 dias de `pg_dump` ainda contêm o dado. Para MVP acadêmico isso é aceitável (disclaimer + finalidade educacional), mas pós-handoff comercial vira item de compliance. **Mitigação:** registrar em `docs/lgpd-impact-assessment.md` como gap consciente; ARCA Ensina decide se quer pipeline de purge em backups.
4. **Service Worker update strategy:** decidido `registerType: 'prompt'` no `vite-plugin-pwa` mas a UX do prompt (toast vs modal vs banner) está apenas sugerida. **Mitigação:** spec do componente `<UpdatePromptToast />` no Sprint 3 dentro de EXP-001b/c.

**Nice-to-Have Gaps:**

1. **i18n estruturado:** strings vivem em `locales/pt-BR/` mas sem lib (`react-i18next`/`@formatjs/intl`). Para MVP (pt-BR único), não é prejuízo. Trajetória OSS pós-MVP pode adicionar.
2. **Storybook:** descopado conscientemente; pode beneficiar onboarding de novos devs no design system, mas custo > ROI no escopo de 8 semanas.
3. **Distributed tracing (OpenTelemetry):** fora do MVP; Sentry breadcrumbs cobrem 80% do uso prático sem essa complexidade.
4. **Manutenção do bulário pós-handoff:** open question persistente; arquitetura suporta autoria via Django admin ou JSON seed.

### Validation Issues Addressed

Todos os Important Gaps acima estão registrados como **ADRs futuros ou decisões pós-MVP**, com mitigação de curto prazo aceitável; nenhum bloqueia início ou continuidade dos sprints.

### Architecture Completeness Checklist

**Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** **READY WITH MINOR GAPS**

Todos os 16 itens da checklist estão `[x]` e **não há Critical Gaps**, mas há 4 Important Gaps explicitamente reconhecidos (algoritmo de sugestão CORE-008, versionamento de disclaimer, LGPD-vs-backup pós-handoff, UX do SW update prompt) que devem ser fechados como **ADRs específicos** no início dos sprints onde se manifestam (Sprint 3 para sugestão e SW prompt; Sprint 4 para versionamento de disclaimer; pós-MVP para LGPD-vs-backup). Nenhum bloqueia Sprint 1 nem invalida a arquitetura geral.

**Confidence Level:** **alta** — decisões alinhadas com brownfield existente, NFRs todos endereçados, cobertura de FRs explícita, paridade engine resolvida por construção (schema declarativo) + automação (suite de paridade no CI).

**Key Strengths:**

1. **Schema declarativo + engine dual com paridade testada** elimina a maior fonte de risco arquitetural (divergência online/offline em domínio safety-critical) por construção.
2. **Cross-cutting concerns em pontos canônicos** (AuditableMixin, ConsentLog, anonimização middleware, `<EducationalDisclaimer/>`) — uma vez certos, certos para sempre.
3. **Defesa em camadas** em todos os pontos de risco: imutabilidade (3 camadas), validação (4 níveis), idempotência (UUID + DB constraint + retry budget), XSS (CSP + ESLint + Zod sanitization).
4. **Stack brownfield preservada** — zero retrabalho destrutivo durante desenvolvimento paralelo de CORE-002a/003/007.
5. **Mapeamento story→diretório explícito** torna trivial planejar PRs e revisar ownership.
6. **3 trajetórias pós-MVP arquiteturalmente viáveis** (comercial, ensino, open-source) sem reescrita estrutural — declaração explícita do PRD honrada pela arquitetura.

**Areas for Future Enhancement (registradas para pós-MVP):**

- Migração JWT localStorage → httpOnly cookie + CSRF (vetor para trajetória comercial).
- Pipeline LGPD de purge em backups (compliance comercial).
- Distributed tracing (OpenTelemetry) e managed Postgres com replicação.
- Storybook + design tokens em pacote npm separável.
- i18n estruturado com `react-i18next`.
- UI dedicada para autoria clínica (substitui Django admin).
- Push notifications, alertas de interação medicamentosa, busca global unificada (já listadas como Growth no PRD).

### Implementation Handoff

**AI Agent Guidelines:**

- **Toda decisão arquitetural neste documento é vinculante.** Desvios precisam de ADR explícito em `docs/adr/` aprovado pelo Tech Lead antes do PR mergear.
- **Padrões de implementação são DoD de PR.** ESLint/ruff/commitlint/coverage thresholds bloqueiam merge em violação.
- **Estrutura de projeto é canônica.** Novos arquivos e diretórios seguem o layout deste documento; criar fora dele exige justificativa em ADR.
- **Cross-cutting concerns têm dono único:** aplicar `AuditableMixin` em todo ViewSet sensível, validar com JSONSchema toda mutação de `steps_data`/`panel_data`, registrar consentimento em `ConsentLog`, propagar `request_id` em logs e respostas.
- **Em domínio safety-critical (calculator, protocol engine, sedation), Tech Lead em pair programming** — não revisão assíncrona apenas.
- **Quando em dúvida, ler este documento.** Se a resposta não estiver aqui, é gap — registrar como ADR ou levantar com Tech Lead antes de codar.

**First Implementation Priority:**

Workshop pré-Sprint-1 (1 dia, autor clínico + Vinicius + Tech Lead + Larissa + Gabriel) para produzir os JSONs de fixture validados de Dengue (`steps_data`) e Sedação (`panel_data`) em `fixtures/protocols/{dengue_guiado.json, sedacao_painel.json}`. Sem isso, CORE-002a, CORE-003 e PAINEL-001 não conseguem fechar Sprint 1.

**Próximos passos imediatos paralelos ao workshop:**

1. **BE Sprint 1:** finalizar CORE-002a (`apps/protocols/engine/`), CORE-003 (`apps/calculator/` + edge_cases.yaml), CORE-007 (`apps/patients/`).
2. **FE Sprint 1:** scaffold `tailwind.config.ts` com tokens ARCA + copiar shadcn primitives base + setup Zustand/React Query/Zod + criar `lib/api/client.ts` com auto-refresh + Husky/commitlint.
3. **Infra:** criar `.github/workflows/{ci,parity,lighthouse,coverage}.yml`; abrir 5 ADRs iniciais (engine dual, schema declarativo, versionamento imutável, AuditableMixin, pipeline LGPD).
