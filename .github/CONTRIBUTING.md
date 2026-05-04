# Guia de contribuição — Arca Ensina

Este documento ensina como rodar o projeto localmente e fazer um teste de fumaça (smoke test) manual de ponta a ponta.

> Ainda **não há testes automatizados** — `accounts/tests.py` é só o stub do Django. A seção "Smoke test" abaixo descreve o caminho atual de validação manual.

## Sumário

1. [Pré-requisitos](#pré-requisitos)
2. [Visão geral do repositório](#visão-geral-do-repositório)
3. [Setup do backend (Django)](#setup-do-backend-django)
4. [Setup do frontend (React + Vite)](#setup-do-frontend-react--vite)
5. [Rodando tudo junto](#rodando-tudo-junto)
6. [Smoke test manual](#smoke-test-manual)
7. [Comandos úteis](#comandos-úteis)
8. [Adicionando um domínio novo](#adicionando-um-domínio-novo)
9. [Convenções](#convenções)
10. [Problemas comuns](#problemas-comuns)

---

## Pré-requisitos

| Ferramenta | Versão mínima | Por quê |
|---|---|---|
| **Python** | 3.12+ | Django 6 exige 3.12 |
| **Node.js** | 20.19+ ou 22.12+ | Exigência do Vite 8 |
| **npm** | 10+ | Vem com o Node |
| **git** | qualquer recente | — |

Para verificar:

```bash
python3 --version    # >= 3.12
node --version       # >= 20.19
npm --version
```

> **Sobre o banco de dados:** o projeto usa **SQLite** em desenvolvimento — não precisa instalar PostgreSQL/MySQL. O arquivo `db.sqlite3` é criado automaticamente.

---

## Visão geral do repositório

```
Arca_Ensina/
├── manage.py                ← entry point do Django
├── requirements.txt         ← dependências Python
├── db.sqlite3               ← banco de dev (não comitar dados reais)
│
├── project/                 ← projeto Django (settings, urls)
│   ├── settings.py
│   └── urls.py              ← rotas /api/v1/...
│
├── accounts/                ← app de autenticação e usuários
│   ├── models.py            ← User customizado (com campo `profile`)
│   ├── serializers.py       ← UserSerializer, RegisterSerializer
│   ├── views.py             ← RegisterView, UserMeView, LogoutView
│   ├── permissions.py       ← IsDoctor, IsAdmin, IsResearcher
│   └── tests.py             ← (vazio — testes virão depois)
│
│   *Cada novo domínio (protocolos, bulário, calculadora, repositório
│   acadêmico, etc.) entra como um app Django próprio neste nível —
│   veja "Adicionando um domínio novo" abaixo.*
│
└── frontend/                ← SPA React + TypeScript + Vite
    ├── index.html
    ├── package.json
    ├── vite.config.ts       ← proxy /api → :8000
    ├── tsconfig*.json
    ├── eslint.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── pages/           ← Login, Register, Dashboard
        ├── context/         ← AuthContext (login, register, logout)
        ├── services/api.ts  ← axios com interceptors JWT
        └── types/auth.ts
```

---

## Setup do backend (Django)

A partir da raiz do repositório:

### 1. Criar e ativar o ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Fish shell:** use `source .venv/bin/activate.fish`
> **Windows (PowerShell):** use `.venv\Scripts\Activate.ps1`

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Aplicar migrações

```bash
python manage.py migrate
```

Isso cria o `db.sqlite3` (se ainda não existir) e aplica todas as migrations — incluindo as do modelo de `User` customizado, JWT blacklist, etc.

### 4. (Opcional) Criar um superusuário para o admin

```bash
python manage.py createsuperuser
```

Útil para acessar `http://localhost:8000/admin/` e inspecionar usuários, tokens, etc.

### 5. Subir o servidor de desenvolvimento

```bash
python manage.py runserver
```

O backend fica em **http://localhost:8000**. Endpoints disponíveis:

| Método | URL | Descrição |
|---|---|---|
| POST | `/api/v1/auth/login/` | Retorna `access` + `refresh` JWT |
| POST | `/api/v1/auth/refresh/` | Renova o `access` token |
| POST | `/api/v1/auth/register/` | Cria conta (auto-login: retorna tokens) |
| GET | `/api/v1/auth/user/` | Dados do usuário autenticado |
| POST | `/api/v1/auth/logout/` | Invalida o `refresh` token |
| GET | `/admin/` | Django admin |

---

## Setup do frontend (React + Vite)

Em **outro terminal** (deixe o backend rodando):

```bash
cd frontend
npm install
npm run dev
```

O frontend fica em **http://localhost:5173**.

> **Importante:** acesse sempre `:5173` no navegador, não `:8000`. O Vite tem um proxy (`vite.config.ts`) que repassa qualquer chamada para `/api/...` ao Django na `:8000` — isso evita problemas de CORS no dev.

---

## Rodando tudo junto

Você precisa de **dois terminais** abertos simultaneamente:

| Terminal 1 (raiz) | Terminal 2 (`frontend/`) |
|---|---|
| `source .venv/bin/activate` | `npm run dev` |
| `python manage.py runserver` | |
| Backend em `:8000` | Frontend em `:5173` |

Sempre abra o navegador em **http://localhost:5173**.

---

## Smoke test manual

Roteiro de ponta a ponta para validar que tudo está funcionando depois de uma mudança grande (atualização de dependências, alteração de auth, etc.):

### 1. Cadastro

1. Abra http://localhost:5173 — você deve cair na tela de login.
2. Clique em **"Cadastre-se"**.
3. Preencha:
   - Usuário: `teste`
   - E-mail: `teste@example.com`
   - Senha: `senhaforte123` (mínimo 8 caracteres)
   - Perfil: `Médico`
4. Clique em **Cadastrar** — você deve ser redirecionado para o `/dashboard`.

> **Observação:** o backend rejeita auto-cadastro com perfil `admin` ou `pesquisador` (`accounts/serializers.py:36`). Esses perfis precisam ser atribuídos manualmente via Django admin.

### 2. Logout e login

1. No dashboard, clique em **Sair**.
2. Faça login com as credenciais que você acabou de criar.
3. Confirme que o dashboard mostra "Bem-vindo, teste!" e o perfil correto.

### 3. Conferência no DevTools

Com a aba **Network** aberta:

1. Faça login → você deve ver um `POST /api/v1/auth/login/` retornando **200** com JSON `{ "access": "...", "refresh": "..." }`.
2. Logo depois, um `GET /api/v1/auth/user/` com header `Authorization: Bearer <access>` retornando **200**.
3. No **Application → Local Storage**, confirme que `access_token` e `refresh_token` foram salvos.
4. Faça logout → confirme `POST /api/v1/auth/logout/` retornando **204** e o local storage sendo limpo.

### 4. Refresh automático (avançado)

O `access` token expira em 15 minutos (`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME` em `project/settings.py:150`). O frontend (`src/services/api.ts`) tenta um refresh automático ao receber 401. Para forçar:

1. Abra DevTools → Application → Local Storage.
2. Apague manualmente o `access_token` (mantenha o `refresh_token`).
3. Recarregue a página — o app deve fazer um `POST /api/v1/auth/refresh/`, salvar um novo `access_token` e continuar autenticado.

### 5. Build de produção (opcional)

Para validar que o bundle de produção também funciona:

```bash
cd frontend
npm run build
npm run preview
```

Abra http://localhost:4173 e repita os passos 1–3.

> **Atenção:** no `preview` **não há proxy do Vite**. As chamadas a `/api/...` vão ser feitas para `:4173` e vão dar 404 (a menos que o Django esteja servindo na mesma origem). Em produção, isso é resolvido via CORS ou colocando frontend e backend na mesma origem — fora do escopo deste guia.

---

## Comandos úteis

### Backend

```bash
python manage.py makemigrations    # gera migrations a partir de mudanças nos models
python manage.py migrate           # aplica migrations
python manage.py createsuperuser   # cria conta admin
python manage.py shell             # REPL com o ORM carregado
python manage.py runserver         # inicia servidor de dev (:8000)
```

### Frontend (a partir de `frontend/`)

```bash
npm run dev          # dev server com HMR (:5173)
npm run typecheck    # tsc --noEmit em todo o projeto
npm run lint         # ESLint
npm run build        # tsc + vite build → dist/
npm run preview      # serve o dist/ em :4173
```

> Antes de abrir um PR, rode pelo menos `npm run typecheck && npm run lint && npm run build` no frontend.

---

## Adicionando um domínio novo

**Regra:** cada domínio do produto vira um **app Django próprio**. Não empilhe models, views ou serializers de domínios diferentes em `accounts/` (nem em qualquer outro app já existente). Apps separados deixam responsabilidades claras, simplificam testes e permitem que vários devs trabalhem em paralelo sem conflito.

### Domínios planejados

Quando forem implementados, cada um vira o seu próprio app:

| Domínio | App sugerido |
|---|---|
| Protocolos clínicos | `protocols/` |
| Repositório acadêmico | `library/` |
| Bulário (consulta de medicamentos) | `bulario/` |
| Calculadora de doses | `calculator/` |

### Passo a passo

A partir da raiz do repositório, com o `.venv` ativo:

```bash
python manage.py startapp <nome_do_app>
```

Isso cria a estrutura padrão (`models.py`, `views.py`, `apps.py`, `migrations/`, etc.). Em seguida:

1. **Registrar o app** em `project/settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'accounts',
       '<nome_do_app>',
   ]
   ```

2. **Definir os models** em `<nome_do_app>/models.py`. Para referenciar o usuário, **sempre** use `settings.AUTH_USER_MODEL`, nunca importe `User` direto:
   ```python
   from django.conf import settings
   from django.db import models

   class Protocol(models.Model):
       author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
       # ...
   ```

3. **Criar serializers** (`<nome_do_app>/serializers.py`) e **views** (`<nome_do_app>/views.py`) seguindo o padrão de `accounts/`.

4. **Criar `<nome_do_app>/urls.py`** com as rotas do domínio:
   ```python
   from django.urls import path
   from .views import MinhaView

   urlpatterns = [
       path('exemplo/', MinhaView.as_view()),
   ]
   ```

5. **Incluir o roteador no `project/urls.py`** sob o prefixo `/api/v1/<dominio>/`:
   ```python
   from django.urls import include, path

   urlpatterns = [
       # ...
       path('api/v1/<dominio>/', include('<nome_do_app>.urls')),
   ]
   ```

6. **Gerar e aplicar migrations:**
   ```bash
   python manage.py makemigrations <nome_do_app>
   python manage.py migrate
   ```

7. **Registrar models no admin** (`<nome_do_app>/admin.py`) se fizer sentido.

8. **No frontend**, defina os tipos em `frontend/src/types/<dominio>.ts` e crie funções de API em `frontend/src/services/<dominio>.ts` reusando o cliente axios já configurado:
   ```ts
   import api from './api'
   import type { Protocol } from '../types/protocols'

   export const listProtocols = () => api.get<Protocol[]>('protocols/')
   ```

### O que NÃO fazer

- ❌ **Não importe `User` direto** de `accounts.models`. Use `settings.AUTH_USER_MODEL` em ForeignKeys e `get_user_model()` quando precisar da classe em runtime.
- ❌ **Não misture domínios** num mesmo app só porque "é só um model pequeno". Comece o app, mesmo que ele tenha um único model.
- ❌ **Não duplique permissões.** Se uma permissão (`IsDoctor`, `IsAdmin`, `IsResearcher`) já existe em `accounts/permissions.py`, importe de lá.

---

## Convenções

### Mensagens de commit

Seguimos um estilo próximo de Conventional Commits, com escopo:

```
feat(infra-001): add JWT auth, permission classes and auth endpoints
fix: deployment issues
```

Tipos comuns: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`.

### Branches

- `main` — branch estável.
- `dev` — branch de integração (atual).
- Para uma nova feature, ramifique a partir de `dev`: `git checkout -b feat/<descrição-curta>`.

### Estilo de código

- **Python:** convenções do Django/PEP-8.
- **TypeScript/React:** o ESLint (`frontend/eslint.config.js`) é a fonte da verdade. Se um lint falhar, rode `npm run lint` localmente antes de fazer commit.
- **Tipos no frontend:** quando adicionar uma chamada nova à API, defina o tipo de resposta em `frontend/src/types/` ou junto à função, e use `api.get<MeuTipo>(...)` / `api.post<MeuTipo>(...)`.

---

## Problemas comuns

### "CORS error" no navegador

Você provavelmente está acessando o backend direto (`http://localhost:8000/...`) em vez do frontend (`http://localhost:5173`). Use sempre `:5173` no dev — o proxy do Vite cuida do resto.

### `405 Method Not Allowed` em `/api/v1/auth/login/`

Você abriu a URL direto na barra do navegador (que faz GET). Login só aceita `POST`. Use a tela de login do frontend, ou `curl -X POST`.

### `python: command not found`

Use `python3` no lugar de `python`, ou ative o venv (`source .venv/bin/activate`).

### `npm install` falhando com `EBADENGINE`

Sua versão do Node está abaixo de 20.19. Atualize com nvm: `nvm install 20 && nvm use 20`.

### Backend está rodando mas o login dá erro

Verifique se as migrations foram aplicadas: `python manage.py migrate`. O modelo `User` é customizado — sem as migrations, a tabela de usuários não existe.

### Quero resetar tudo

```bash
# backend: apaga banco e recria
rm db.sqlite3
python manage.py migrate

# frontend: limpa node_modules e dist
cd frontend
rm -rf node_modules dist package-lock.json
npm install
```
