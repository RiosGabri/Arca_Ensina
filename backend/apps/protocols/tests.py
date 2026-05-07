from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Protocol, ProtocolVersion

User = get_user_model()


class ProtocolModelTest(TestCase):

    def test_create_protocol_creates_first_version(self):
        protocol = Protocol.objects.create(title="Teste Protocolo")
        self.assertEqual(protocol.versions.count(), 1)
        version = protocol.versions.first()
        self.assertEqual(version.version_number, 1)
        self.assertTrue(version.is_current)

    def test_protocol_str(self):
        protocol = Protocol.objects.create(title="Dengue")
        self.assertEqual(str(protocol), "Dengue")


class ProtocolVersionModelTest(TestCase):

    def setUp(self):
        self.protocol = Protocol.objects.create(title="Protocolo Teste")

    def test_unique_constraint_protocol_version_number(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ProtocolVersion.objects.create(
                protocol=self.protocol,
                version_number=1,
                is_current=False,
            )

    def test_is_current_disables_previous(self):
        v1 = self.protocol.versions.first()
        self.assertTrue(v1.is_current)

        v2 = ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            is_current=True,
        )

        v1.refresh_from_db()
        self.assertFalse(v1.is_current)
        self.assertTrue(v2.is_current)

    def test_auto_increment_version_number(self):
        v1 = self.protocol.versions.first()
        self.assertEqual(v1.version_number, 1)

        v2 = ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            is_current=False,
        )
        self.assertEqual(v2.version_number, 2)

    def test_save_with_steps_data(self):
        steps = {"steps": [{"id": "step_0", "type": "info", "title": "Teste"}]}
        v = ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            protocol_type="guiado",
            steps_data=steps,
        )
        self.assertEqual(v.steps_data["steps"][0]["title"], "Teste")


class ProtocolSerializerTest(TestCase):

    def setUp(self):
        self.protocol = Protocol.objects.create(title="Protocolo Serializer")
        self.version = self.protocol.versions.first()

    def test_protocol_serializer_current_version(self):
        from .serializers import ProtocolSerializer

        serializer = ProtocolSerializer(self.protocol)
        data = serializer.data
        self.assertIsNotNone(data["current_version"])
        self.assertEqual(data["current_version"]["version_number"], 1)

    def test_protocol_list_serializer_no_heavy_fields(self):
        from .serializers import ProtocolListSerializer

        serializer = ProtocolListSerializer(self.protocol)
        data = serializer.data
        self.assertNotIn("steps_data", data)
        self.assertNotIn("panel_data", data)

    def test_version_create_serializer_auto_increment(self):
        from .serializers import ProtocolVersionCreateSerializer

        data = {
            "protocol": self.protocol.pk,
            "protocol_type": "guiado",
            "steps_data": {"steps": []},
        }
        serializer = ProtocolVersionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        version = serializer.save()
        self.assertEqual(version.version_number, 2)

    def test_version_create_serializer_copies_previous_data(self):
        from .serializers import ProtocolVersionCreateSerializer

        self.version.steps_data = {"steps": [{"id": "step_0"}]}
        self.version.protocol_type = "guiado"
        self.version.save()

        data = {"protocol": self.protocol.pk}
        serializer = ProtocolVersionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        version = serializer.save()
        self.assertEqual(version.steps_data, {"steps": [{"id": "step_0"}]})


class ProtocolViewSetTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            profile="admin",
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@test.com",
            password="testpass123",
            profile="medico",
        )
        self.researcher = User.objects.create_user(
            username="researcher",
            email="researcher@test.com",
            password="testpass123",
            profile="pesquisador",
        )
        self.protocol = Protocol.objects.create(title="Protocolo ViewSet")

    def test_list_requires_authentication(self):
        response = self.client.get("/api/v1/protocols/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_list(self):
        self.client.force_authenticate(user=self.researcher)
        response = self.client.get("/api/v1/protocols/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_can_retrieve(self):
        self.client.force_authenticate(user=self.researcher)
        response = self.client.get(f"/api/v1/protocols/{self.protocol.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        data = {"title": "Novo Protocolo", "specialty": "Cardiologia"}
        response = self.client.post("/api/v1/protocols/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_doctor_cannot_create(self):
        self.client.force_authenticate(user=self.doctor)
        data = {"title": "Novo Protocolo"}
        response = self.client.post("/api/v1/protocols/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update(self):
        self.client.force_authenticate(user=self.admin)
        data = {"title": "Protocolo Atualizado"}
        response = self.client.patch(f"/api/v1/protocols/{self.protocol.pk}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_doctor_cannot_update(self):
        self.client.force_authenticate(user=self.doctor)
        data = {"title": "Protocolo Atualizado"}
        response = self.client.patch(f"/api/v1/protocols/{self.protocol.pk}/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/protocols/{self.protocol.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_versions_action(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(f"/api/v1/protocols/{self.protocol.pk}/versions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_diff_action(self):
        self.client.force_authenticate(user=self.doctor)
        ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            is_current=True,
        )
        response = self.client.get(
            f"/api/v1/protocols/{self.protocol.pk}/diff/?from=1&to=2"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)

    def test_diff_missing_params(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(f"/api/v1/protocols/{self.protocol.pk}/diff/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProtocolVersionViewSetTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin2",
            email="admin2@test.com",
            password="testpass123",
            profile="admin",
        )
        self.doctor = User.objects.create_user(
            username="doctor2",
            email="doctor2@test.com",
            password="testpass123",
            profile="medico",
        )
        self.protocol = Protocol.objects.create(title="Protocolo Version ViewSet")
        self.version = self.protocol.versions.first()

    def test_doctor_can_list_versions(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get("/api/v1/protocol-versions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_version(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "protocol": self.protocol.pk,
            "protocol_type": "guiado",
            "steps_data": {"steps": []},
        }
        response = self.client.post("/api/v1/protocol-versions/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_doctor_cannot_create_version(self):
        self.client.force_authenticate(user=self.doctor)
        data = {"protocol": self.protocol.pk}
        response = self.client.post("/api/v1/protocol-versions/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_current_action(self):
        self.client.force_authenticate(user=self.admin)
        v2 = ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            is_current=False,
        )
        response = self.client.post(f"/api/v1/protocol-versions/{v2.pk}/set-current/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        v2.refresh_from_db()
        self.version.refresh_from_db()
        self.assertTrue(v2.is_current)
        self.assertFalse(self.version.is_current)

    def test_filter_by_protocol_type(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get("/api/v1/protocol-versions/?protocol_type=guiado")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FixtureLoadTest(TestCase):

    def test_dengue_fixture_structure(self):
        import json
        from pathlib import Path

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["model"], "protocols.protocol")
        self.assertEqual(data[1]["model"], "protocols.protocolversion")

        steps_data = data[1]["fields"]["steps_data"]
        self.assertIn("steps", steps_data)
        self.assertGreater(len(steps_data["steps"]), 0)

        valid_types = {
            "info", "yes_no", "multiple_choice", "checklist",
            "numeric_input", "derived_calc", "medication_prescription",
            "wait_reassess", "titration_loop",
        }
        for step in steps_data["steps"]:
            self.assertIn(step["type"], valid_types, f"Invalid type: {step['type']}")

    def test_sedacao_fixture_structure(self):
        import json
        from pathlib import Path

        fixture_path = Path(__file__).parent / "fixtures" / "sedacao_painel.json"
        with open(fixture_path) as f:
            data = json.load(f)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["model"], "protocols.protocol")
        self.assertEqual(data[1]["model"], "protocols.protocolversion")

        panel_data = data[1]["fields"]["panel_data"]
        self.assertIn("sections", panel_data)
        self.assertIn("calculators", panel_data)
        self.assertGreater(len(panel_data["sections"]), 0)
        self.assertGreater(len(panel_data["calculators"]), 0)
