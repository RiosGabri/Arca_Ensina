# Arquitetura — Arca Ensina

Referência técnica da infraestrutura implementada. Para setup e contribuição, veja `.github/CONTRIBUTING.md`.

---

## Visão geral

```
backend/
├── project/                 Settings, URLs, configs globais
│   ├── settings.py          DRF, JWT, throttle, paginação
│   ├── urls.py              Todas as rotas /api/v1/...
│   ├── exceptions.py        Exception handler (JSON padronizado)
│   └── serializers.py       BaseSerializer
├── apps/
│   ├── accounts/            Auth e usuários
│   │   ├── models.py        Custom User (AbstractUser + profile)
│   │   ├── views.py         Register, UserMe, Logout
│   │   ├── serializers.py   UserSerializer, RegisterSerializer
│   │   └── permissions.py   IsDoctor, IsAdmin, IsResearcher
│   └── audit/               Auditoria
│       ├── models.py        AuditLog (UUID, action, resource, IP, payload)
│       ├── mixins.py        AuditableMixin (auto-log CRUD)
│       ├── utils.py         log_audit() para logging manual
│       ├── filters.py       Filtros por action, user, resource, datas
│       └── views.py         AuditLogViewSet (read-only, admin-only)
├── manage.py
├── requirements.txt
└── Dockerfile

frontend/                    React + Vite + TypeScript
├── src/pages/               Login, Register, Dashboard
├── src/context/             AuthContext
├── src/services/api.ts      Axios com interceptors JWT
└── src/types/auth.ts        User, AuthTokens, ApiErrorResponse

docker-compose.yml           Orquestra backend + frontend + PostgreSQL
.github/workflows/           CI (lint + test + build) e deploy staging
```

---

## Auth e permissões (INFRA-001)

### Custom User

```python
class User(AbstractUser):
    email = EmailField(unique=True)
    profile = CharField(choices=['medico', 'admin', 'pesquisador'], default='medico')
```

`AUTH_USER_MODEL = 'accounts.User'` — sempre use `settings.AUTH_USER_MODEL` em ForeignKeys.

### JWT

- Access token: 15 minutos
- Refresh token: 7 dias (com rotação)
- Logout faz blacklist do refresh token

### Permission classes

| Classe | Perfil permitido | Superuser |
|---|---|---|
| `IsDoctor` | `medico` | Sim |
| `IsAdmin` | `admin` | Sim |
| `IsResearcher` | `pesquisador` | Sim |

```python
from apps.accounts.permissions import IsDoctor

class MeuViewSet(viewsets.ModelViewSet):
    permission_classes = [IsDoctor]
```

### Registro

Auto-cadastro aceita apenas perfil `medico`. Perfis `admin` e `pesquisador` são atribuídos via Django admin.

---

## DRF base (INFRA-003)

### Configurações globais

| Config | Valor |
|---|---|
| Versionamento | `URLPathVersioning` — `/api/v1/` |
| Paginação | `PageNumberPagination`, 20 itens |
| Throttle anon | 100/hora |
| Throttle auth | 1000/hora |
| Filtros | `DjangoFilterBackend` |
| Docs | `/api/docs/` (Swagger), `/api/schema/` (OpenAPI) |

### Formato de erro

Todas as exceções DRF são convertidas para:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Descrição do erro",
    "details": { "campo": ["mensagem"] }
  }
}
```

Códigos: `validation_error` (400), `authentication_error` (401), `permission_denied` (403), `not_found` (404), `throttled` (429), `server_error` (500).

**Regra:** sempre use exceções do DRF (`raise ValidationError(...)`) em vez de `return Response(..., status=400)`.

### Consumindo erros no frontend

O tipo `ApiErrorResponse` em `frontend/src/types/auth.ts` espelha este formato. Ao tratar erros de API:

```typescript
import type { ApiErrorResponse } from '../types/auth'

catch (err) {
  if (err instanceof AxiosError) {
    const data = err.response?.data as ApiErrorResponse | undefined
    // Mensagem legível:
    const message = data?.error?.message
    // Erros de validação por campo (400):
    const fieldErrors = data?.error?.details
  }
}
```

**Nunca renderize `data.error` diretamente** — é um objeto `{code, message}`, não uma string. Use `data.error.message`.

### BaseSerializer

Herdar de `project.serializers.BaseSerializer` adiciona `created_at`, `updated_at` e `version` como read-only. O model precisa definir esses campos:

```python
# model
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
version = models.PositiveIntegerField(default=1)

# serializer
from project.serializers import BaseSerializer

class MeuSerializer(BaseSerializer):
    class Meta:
        model = MeuModel
        fields = ['id', 'titulo', 'created_at', 'updated_at', 'version']
```

---

## Auditoria (INFRA-002)

### AuditableMixin

Adicione a qualquer `ModelViewSet` para logar automaticamente CREATE, UPDATE, DELETE, LIST e RETRIEVE:

```python
from apps.audit.mixins import AuditableMixin

class ProtocolViewSet(AuditableMixin, ModelViewSet):
    audit_resource_type = 'protocol'   # obrigatório
    queryset = Protocol.objects.all()
    serializer_class = ProtocolSerializer
```

`AuditableMixin` deve vir **antes** de `ModelViewSet` na herança.

### Logging manual

Para ações fora de viewsets:

```python
from apps.audit.utils import log_audit

log_audit(
    user=request.user,
    action='CALCULATE',
    resource_type='drug_calculator',
    resource_id='',
    ip=request.META.get('REMOTE_ADDR'),
    payload={'weight': 70, 'result': 700},
)
```

### Endpoint de consulta

`GET /api/v1/audit/` — somente admin. Filtros: `action`, `user`, `resource_type`, `date_from`, `date_to`. Retenção: 90 dias.

---

## Exemplo completo: novo domínio

```python
# backend/apps/protocols/models.py
from django.db import models

class Protocol(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

# backend/apps/protocols/serializers.py
from project.serializers import BaseSerializer
from .models import Protocol

class ProtocolSerializer(BaseSerializer):
    class Meta:
        model = Protocol
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'version']

# backend/apps/protocols/views.py
from rest_framework.viewsets import ModelViewSet
from apps.accounts.permissions import IsDoctor
from apps.audit.mixins import AuditableMixin
from .models import Protocol
from .serializers import ProtocolSerializer

class ProtocolViewSet(AuditableMixin, ModelViewSet):
    audit_resource_type = 'protocol'
    queryset = Protocol.objects.all()
    serializer_class = ProtocolSerializer
    permission_classes = [IsDoctor]

# backend/apps/protocols/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProtocolViewSet

router = DefaultRouter()
router.register(r'protocols', ProtocolViewSet, basename='protocol')
urlpatterns = router.urls

# backend/project/urls.py — adicionar:
# path(f'{V}/', include('apps.protocols.urls')),
```

---

## Testes

```python
from rest_framework.test import APIClient
from apps.accounts.models import User

class MeuTesteBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doctor = User.objects.create_user(
            username='doc', email='doc@test.com',
            password='pass1234', profile='medico',
        )

    def _auth(self, user):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': user.username, 'password': 'pass1234',
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
```

O que testar em cada feature:
- Auth obrigatória (401 sem token)
- Permissão negada para perfil errado (403)
- Validação de campos (400 com formato de erro padrão)
- Auditoria (verificar `AuditLog.objects.filter(...)`)
- Paginação (`count`, `results`, `next`, `previous`)

---

## Checklist para novas features

- [ ] Model com `created_at`, `updated_at`, `version`
- [ ] Serializer herda `BaseSerializer`
- [ ] ViewSet usa `AuditableMixin` e define `audit_resource_type`
- [ ] Permission class adequada (`IsDoctor`, `IsAdmin`, `IsResearcher`)
- [ ] Erros via exceções DRF (não `Response` com status de erro)
- [ ] URLs sob `f'{V}/...'` (ver `backend/project/urls.py`)
- [ ] Frontend usa `ApiErrorResponse` para tipar erros de API (nunca renderizar `error` como string)
- [ ] Testes cobrindo auth, permissões, validação, auditoria
