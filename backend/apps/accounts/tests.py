from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIClient

from .models import User
from .permissions import IsDoctor


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"

    def test_register_blocks_admin_profile(self):
        resp = self.client.post(
            self.url,
            {
                "username": "adminuser",
                "email": "admin@example.com",
                "password": "strongpass123",
                "profile": "admin",
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_register_blocks_pesquisador_profile(self):
        resp = self.client.post(
            self.url,
            {
                "username": "researcher",
                "email": "researcher@example.com",
                "password": "strongpass123",
                "profile": "pesquisador",
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_register_allows_medico_profile(self):
        resp = self.client.post(
            self.url,
            {
                "username": "doctor1",
                "email": "doctor1@example.com",
                "password": "strongpass123",
                "profile": "medico",
            },
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_email_uniqueness(self):
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="strongpass123",
        )
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "dup@example.com",
                "password": "strongpass123",
                "profile": "medico",
            },
        )
        self.assertEqual(resp.status_code, 400)


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
            username="testlogin",
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
            {"username": "testlogin", "password": "strongpass123"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_logout_blacklists_refresh_token(self):
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"username": "testlogin", "password": "strongpass123"},
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
            username="otheruser",
            email="other@example.com",
            password="strongpass123",
            profile="medico",
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        other_refresh = str(RefreshToken.for_user(other))

        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"username": "testlogin", "password": "strongpass123"},
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
            {"username": "testlogin", "password": "strongpass123"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )
        resp = self.client.post("/api/v1/auth/logout/", {})
        self.assertEqual(resp.status_code, 400)

    def test_user_me_returns_authenticated_user(self):
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"username": "testlogin", "password": "strongpass123"},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )
        resp = self.client.get("/api/v1/auth/user/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "testlogin")
        self.assertEqual(resp.data["profile"], "medico")
