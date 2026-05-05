# Guia de contribuição — Arca Ensina

Como rodar o projeto localmente e contribuir.

## Pré-requisitos

| Ferramenta | Versão mínima | Por quê |
|---|---|---|
| **Python** | 3.12+ | Django 6 exige 3.12 |
| **Node.js** | 20.19+ ou 22.12+ | Exigência do Vite 8 |
| **npm** | 10+ | Vem com o Node |
| **Docker** (opcional) | 24+ | Para rodar tudo com `docker compose up` |

> **Banco de dados:** SQLite em desenvolvimento — não precisa instalar PostgreSQL. O Docker Compose usa PostgreSQL automaticamente.

---

## Setup

### Opção 1: Docker (recomendado)

```bash
cp .env.example .env             # só na primeira vez
docker compose up                # backend :8000 + frontend :5173 + PostgreSQL
```

Migrations rodam automaticamente na inicialização.

### Opção 2: Manual (dois terminais)

**Backend (Django):**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py runserver       # http://localhost:8000
```

Para criar um admin: `python manage.py createsuperuser`

**Frontend (React + Vite):**

Em outro terminal:

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

> Acesse sempre `:5173` — o Vite faz proxy de `/api/...` para o Django.

---

## Endpoints disponíveis

| Método | URL | Descrição |
|---|---|---|
| POST | `/api/v1/auth/login/` | Retorna `access` + `refresh` JWT |
| POST | `/api/v1/auth/refresh/` | Renova o `access` token |
| POST | `/api/v1/auth/register/` | Cria conta (retorna tokens) |
| GET | `/api/v1/auth/user/` | Dados do usuário autenticado |
| POST | `/api/v1/auth/logout/` | Invalida o `refresh` token |
| GET | `/api/v1/audit/` | Logs de auditoria (somente admin) |
| GET | `/api/docs/` | Documentação OpenAPI (Swagger UI) |
| GET | `/admin/` | Django admin |

---

## Smoke test

1. Abra http://localhost:5173 → tela de login
2. Tente login com senha errada → mensagem de erro visível (sem tela branca)
3. Cadastre-se com perfil Médico (admin/pesquisador são bloqueados no auto-cadastro)
4. Confirme redirecionamento para `/dashboard`
5. Faça logout e login novamente com as credenciais corretas
6. No DevTools (Network): confirme `POST /api/v1/auth/login/` → 200, `GET /api/v1/auth/user/` → 200

---

## Adicionando um domínio novo

Cada domínio vira um **app Django próprio** dentro de `backend/apps/`. Não misture domínios em apps existentes.

```bash
cd backend
python manage.py startapp <nome_do_app> apps/<nome_do_app>
```

Depois:

1. Atualize `name` em `apps/<nome>/apps.py` para `'apps.<nome>'`
2. Registre em `INSTALLED_APPS` (`backend/project/settings.py`) como `'apps.<nome>'`
3. Defina models — use `settings.AUTH_USER_MODEL` para FK de usuário
4. Crie serializers herdando de `project.serializers.BaseSerializer`
5. Crie views com `apps.audit.mixins.AuditableMixin` antes de `ModelViewSet`
6. Crie `urls.py` e inclua em `backend/project/urls.py` sob `api/<str:version>/`
7. Gere e aplique migrations

> Para detalhes sobre a infraestrutura (auth, auditoria, DRF config), veja `docs/architecture.md`.

### O que NÃO fazer

- Não importe `User` direto — use `settings.AUTH_USER_MODEL` / `get_user_model()`
- Não misture domínios num mesmo app
- Não duplique permissões — importe de `apps.accounts.permissions`
- Não retorne `Response` com status de erro — use exceções do DRF (`ValidationError`, `NotFound`, etc.)
- Não renderize `err.response.data.error` diretamente no JSX — é um objeto, use `data.error.message` (tipo `ApiErrorResponse` em `types/auth.ts`)

---

## Convenções

### Commits

Conventional Commits com escopo: `feat(infra-001): add JWT auth`

Tipos: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

### Branches

- `main` — estável
- `dev` — integração
- Features: `git checkout -b feat/<descrição-curta>` a partir de `dev`

### Estilo

- **Python:** PEP-8
- **TypeScript:** ESLint (`npm run lint`)
- Antes de abrir PR: `npm run typecheck && npm run lint && npm run build`

---

## Comandos úteis

```bash
# Backend (a partir de backend/)
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py runserver

# Frontend (a partir de frontend/)
cd frontend
npm run dev
npm run typecheck
npm run lint
npm run build

# Docker (da raiz do projeto)
docker compose up              # subir tudo
docker compose down            # parar tudo
docker compose up --build      # rebuild após mudar Dockerfile/requirements
```

---

## Problemas comuns

| Problema | Solução |
|---|---|
| CORS error no navegador | Acesse `:5173`, não `:8000` |
| 405 em `/api/v1/auth/login/` | Login só aceita POST, não GET |
| `python: command not found` | Use `python3` ou ative o venv |
| `npm install` com `EBADENGINE` | Atualize Node para 20.19+ |
| Login dá erro | Rode `cd backend && python manage.py migrate` |
| `ModuleNotFoundError: apps` | Certifique-se de estar rodando de dentro de `backend/` |
