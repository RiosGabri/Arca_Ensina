from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Invitation, User
from .permissions import IsDoctor


class InvitationCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.invitation = Invitation.objects.create(
            email="convidado@example.com", profile="medico"
        )

    def test_valid_invitation_returns_email_and_profile(self):
        resp = self.client.get(f"/api/v1/auth/invite/{self.invitation.token}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["email"], "convidado@example.com")
        self.assertEqual(resp.data["profile"], "medico")

    def test_unknown_token_returns_404(self):
        resp = self.client.get("/api/v1/auth/invite/inexistente/")
        self.assertEqual(resp.status_code, 404)

    def test_expired_invitation_returns_400(self):
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        resp = self.client.get(f"/api/v1/auth/invite/{self.invitation.token}/")
        self.assertEqual(resp.status_code, 400)

    def test_used_invitation_returns_400(self):
        self.invitation.accepted_at = timezone.now()
        self.invitation.save()
        resp = self.client.get(f"/api/v1/auth/invite/{self.invitation.token}/")
        self.assertEqual(resp.status_code, 400)


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"
        self.invitation = Invitation.objects.create(
            email="novo@example.com", profile="pesquisador"
        )

    def _payload(self, **overrides):
        data = {
            "token": self.invitation.token,
            "first_name": "Ana",
            "last_name": "Silva",
            "gender": "feminino",
            "birth_date": "1990-05-20",
            "password": "strongpass123",
        }
        data.update(overrides)
        return data

    def test_register_with_valid_invitation(self):
        resp = self.client.post(self.url, self._payload())
        self.assertEqual(resp.status_code, 201)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        user = User.objects.get(email="novo@example.com")
        # E-mail e perfil vêm do convite, não do payload.
        self.assertEqual(user.profile, "pesquisador")
        self.assertEqual(user.first_name, "Ana")
        self.assertEqual(user.gender, "feminino")

    def test_register_marks_invitation_as_used(self):
        self.client.post(self.url, self._payload())
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_used)

    def test_register_without_token_fails(self):
        resp = self.client.post(self.url, self._payload(token=""))
        self.assertEqual(resp.status_code, 400)

    def test_register_with_invalid_token_fails(self):
        resp = self.client.post(self.url, self._payload(token="naoexiste"))
        self.assertEqual(resp.status_code, 400)

    def test_register_rejects_reused_invitation(self):
        self.client.post(self.url, self._payload())
        resp = self.client.post(self.url, self._payload())
        self.assertEqual(resp.status_code, 400)

    def test_register_rejects_expired_invitation(self):
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        resp = self.client.post(self.url, self._payload())
        self.assertEqual(resp.status_code, 400)

    def test_register_ignores_payload_email_and_profile(self):
        resp = self.client.post(
            self.url,
            self._payload(email="hacker@example.com", profile="admin"),
        )
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(email="novo@example.com")
        self.assertEqual(user.profile, "pesquisador")
        self.assertFalse(User.objects.filter(email="hacker@example.com").exists())


class PermissionTests(TestCase):
    def test_permission_classes_reject_anonymous(self):
        perm = IsDoctor()
        request = type("FakeRequest", (), {"user": AnonymousUser()})()
        view = type("FakeView", (), {})()
        self.assertFalse(perm.has_permission(request, view))


class AuthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testlogin@example.com",
            password="strongpass123",
            profile="medico",
        )

    def test_user_me_requires_auth(self):
        resp = self.client.get("/api/v1/auth/user/")
        self.assertEqual(resp.status_code, 401)

    def test_login_returns_tokens(self):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "testlogin@example.com", "password": "strongpass123"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_logout_blacklists_refresh_token(self):
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "testlogin@example.com", "password": "strongpass123"},
        )
        refresh = login_resp.data["refresh"]
        access = login_resp.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_resp = self.client.post("/api/v1/auth/logout/", {"refresh": refresh})
        self.assertEqual(logout_resp.status_code, 204)

        refresh_resp = self.client.post("/api/v1/auth/refresh/", {"refresh": refresh})
        self.assertIn(refresh_resp.status_code, (400, 401))

    def test_logout_rejects_other_users_token(self):
        other = User.objects.create_user(
            email="other@example.com",
            password="strongpass123",
            profile="medico",
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        other_refresh = str(RefreshToken.for_user(other))

        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "testlogin@example.com", "password": "strongpass123"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )
        resp = self.client.post("/api/v1/auth/logout/", {"refresh": other_refresh})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["error"]["code"], "permission_denied")
        self.assertEqual(
            resp.data["error"]["message"],
            "Token does not belong to user.",
        )

    def test_logout_without_refresh_returns_400(self):
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "testlogin@example.com", "password": "strongpass123"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )
        resp = self.client.post("/api/v1/auth/logout/", {})
        self.assertEqual(resp.status_code, 400)

    def test_user_me_returns_authenticated_user(self):
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "testlogin@example.com", "password": "strongpass123"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )
        resp = self.client.get("/api/v1/auth/user/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["email"], "testlogin@example.com")
        self.assertEqual(resp.data["profile"], "medico")
