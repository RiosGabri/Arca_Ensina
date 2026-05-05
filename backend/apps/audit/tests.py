from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog


class AuditLogModelTests(TestCase):
    def test_create_audit_log(self):
        log = AuditLog.objects.create(
            action="CREATE",
            resource_type="TestResource",
            resource_id="123",
            ip="127.0.0.1",
            payload={"method": "POST", "path": "/test/"},
        )
        self.assertEqual(log.action, "CREATE")
        self.assertEqual(log.resource_type, "TestResource")
        self.assertEqual(str(log.resource_id), "123")
        self.assertIsNotNone(log.timestamp)


class AuditableMixinTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audittest",
            email="audit@example.com",
            password="strongpass123",
            profile="medico",
        )

    def test_log_audit_helper(self):
        from apps.audit.utils import log_audit

        log_audit(
            user=self.user,
            action="UPDATE",
            resource_type="Patient",
            resource_id="99",
            ip="10.0.0.1",
            payload={"method": "PATCH", "path": "/api/v1/patients/99/"},
        )
        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "UPDATE")
        self.assertEqual(log.payload["method"], "PATCH")

    def test_payload_does_not_contain_body(self):
        from apps.audit.utils import log_audit

        log_audit(
            user=self.user,
            action="CREATE",
            resource_type="Note",
            resource_id="1",
            payload={"method": "POST", "path": "/api/v1/notes/"},
        )
        log = AuditLog.objects.first()
        # Ensure no raw request body or sensitive fields leaked
        self.assertNotIn("password", log.payload)
        self.assertNotIn("cpf", log.payload)
        self.assertIn("method", log.payload)
        self.assertIn("path", log.payload)


class AuditEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="strongpass123",
            profile="admin",
        )
        self.doctor = User.objects.create_user(
            username="docuser",
            email="doc@example.com",
            password="strongpass123",
            profile="medico",
        )
        self.researcher = User.objects.create_user(
            username="researchuser",
            email="research@example.com",
            password="strongpass123",
            profile="pesquisador",
        )
        AuditLog.objects.create(
            user=self.admin,
            action="CREATE",
            resource_type="Protocol",
            resource_id="1",
            ip="127.0.0.1",
            payload={"method": "POST", "path": "/api/v1/protocols/"},
        )
        AuditLog.objects.create(
            user=self.doctor,
            action="LIST",
            resource_type="Protocol",
            resource_id="",
            ip="127.0.0.1",
            payload={"method": "GET", "path": "/api/v1/protocols/"},
        )

    def _login(self, user):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"username": user.username, "password": "strongpass123"},
        )
        return resp.data["access"]

    def test_admin_can_list_audit_logs(self):
        token = self._login(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/v1/audit/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_doctor_cannot_access_audit_logs(self):
        token = self._login(self.doctor)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/v1/audit/")
        self.assertEqual(resp.status_code, 403)

    def test_researcher_cannot_access_audit_logs(self):
        token = self._login(self.researcher)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/v1/audit/")
        self.assertEqual(resp.status_code, 403)

    def test_filter_by_action(self):
        token = self._login(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/v1/audit/?action=CREATE")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["action"], "CREATE")

    def test_filter_by_user(self):
        token = self._login(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(f"/api/v1/audit/?user={self.doctor.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["user"], self.doctor.id)

    def test_filter_by_date_range(self):
        token = self._login(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        today = timezone.now().date().isoformat()
        resp = self.client.get(f"/api/v1/audit/?date_from={today}&date_to={today}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_unauthenticated_cannot_access_audit(self):
        resp = self.client.get("/api/v1/audit/")
        self.assertEqual(resp.status_code, 401)


class CleanAuditLogsCommandTests(TestCase):
    def setUp(self):
        self.old_log = AuditLog.objects.create(
            action="DELETE",
            resource_type="OldResource",
            resource_id="old1",
        )
        AuditLog.objects.filter(id=self.old_log.id).update(
            timestamp=timezone.now() - timedelta(days=100)
        )
        self.old_log.refresh_from_db()

        self.recent_log = AuditLog.objects.create(
            action="CREATE",
            resource_type="NewResource",
            resource_id="new1",
        )
        AuditLog.objects.filter(id=self.recent_log.id).update(
            timestamp=timezone.now() - timedelta(days=10)
        )
        self.recent_log.refresh_from_db()

    def test_command_deletes_old_logs(self):
        call_command("clean_audit_logs", days=90)
        self.assertFalse(AuditLog.objects.filter(id=self.old_log.id).exists())
        self.assertTrue(AuditLog.objects.filter(id=self.recent_log.id).exists())

    def test_command_uses_setting_default(self):
        from django.conf import settings

        self.assertEqual(getattr(settings, "AUDIT_LOG_RETENTION_DAYS", None), 90)
        call_command("clean_audit_logs")
        self.assertFalse(AuditLog.objects.filter(id=self.old_log.id).exists())
        self.assertTrue(AuditLog.objects.filter(id=self.recent_log.id).exists())
