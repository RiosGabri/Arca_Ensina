from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    Protocol,
    ProtocolExecution,
    ProtocolExecutionState,
    ProtocolStep,
    ProtocolVersion,
)
from .services import ProtocolExecutionEngine

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

        self.version.steps_data = {
            "steps": [{"id": "step_0", "type": "info", "title": "Step 0"}]
        }
        self.version.protocol_type = "guiado"
        self.version.save()

        data = {"protocol": self.protocol.pk}
        serializer = ProtocolVersionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        version = serializer.save()
        self.assertEqual(
            version.steps_data,
            {"steps": [{"id": "step_0", "type": "info", "title": "Step 0"}]},
        )


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

        self.passo2 = ProtocolStep.objects.create(
            version=self.version,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=2,
            title="segundo passo"
        )
        self.passo1 = ProtocolStep.objects.create(
            version=self.version,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=1,
            title="primeiro passo"
        )

        self.passo1.next_step=self.passo2
        self.passo1.save()

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
        response = self.client.post("/api/v1/protocol-versions/", data, format="json")
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

    def test_admin_cannot_patch_protocol_version(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/v1/protocol-versions/{self.version.pk}/",
            {"metadata": {"changed": True}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_admin_cannot_delete_protocol_version(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/v1/protocol-versions/{self.version.pk}/",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_execute_start_creates_execution(self):
        self.client.force_authenticate(user=self.doctor)

        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente API"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["patient_name"], "Paciente API")
        self.assertIsNotNone(response.data["current_step"])

    def test_execute_answer_advances_step(self):
        self.client.force_authenticate(user=self.doctor)

        self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "paciente"},
            format="json",
        )

        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/answer/",
            {"values": {"confirmado": True}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_step"]["id"], self.passo2.id)

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
            "info",
            "yes_no",
            "multiple_choice",
            "checklist",
            "numeric_input",
            "derived_calc",
            "medication_prescription",
            "wait_reassess",
            "titration_loop",
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


class ProtocolVersionSchemaValidationTest(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(title="Schema Test")

    def test_dengue_fixture_steps_data_validates_against_schema(self):
        import json
        from pathlib import Path

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        version = ProtocolVersion(
            protocol=self.protocol,
            version_number=2,
            protocol_type=ProtocolVersion.ProtocolType.GUIADO,
            steps_data=data[1]["fields"]["steps_data"],
        )

        version.clean()

    def test_guided_steps_data_requires_step_id(self):
        version = ProtocolVersion(
            protocol=self.protocol,
            version_number=2,
            protocol_type=ProtocolVersion.ProtocolType.GUIADO,
            steps_data={
                "steps": [
                    {
                        "type": "info",
                        "title": "Sem ID",
                    }
                ]
            },
        )

        with self.assertRaises(Exception):
            version.clean()
        
class ProtocolStepModelTest(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(title="Protocolo Step Test")
        self.version = self.protocol.versions.first()

    def _make_step(self, order=1, step_type=None, **kwargs):
        return ProtocolStep.objects.create(
            version=self.version,
            step_type=step_type or ProtocolStep.StepType.INFORMATIVO,
            order=order,
            title=f"Passo {order}",
            **kwargs,
        )

    def test_create_step(self):
        step = self._make_step()
        self.assertEqual(step.version, self.version)
        self.assertEqual(step.step_type, ProtocolStep.StepType.INFORMATIVO)
        self.assertEqual(step.order, 1)

    def test_all_nine_step_types(self):
        for i, step_type in enumerate(ProtocolStep.StepType.values, start=1):
            step = self._make_step(order=i, step_type=step_type)
            self.assertEqual(step.step_type, step_type)

    def test_unique_order_per_version(self):
        from django.db import IntegrityError
        self._make_step(order=1)
        with self.assertRaises(IntegrityError):
            self._make_step(order=1)

    def test_same_order_different_versions(self):
        other_version = ProtocolVersion.objects.create(
            protocol=self.protocol,
            version_number=2,
            is_current=False,
        )
        step1 = self._make_step(order=1)
        step2 = ProtocolStep.objects.create(
            version=other_version,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=1,
            title="Passo 1 v2",
        )
        self.assertNotEqual(step1.pk, step2.pk)

    def test_next_step_self_reference(self):
        step1 = self._make_step(order=1)
        step2 = self._make_step(order=2)
        step1.next_step = step2
        step1.save()
        step1.refresh_from_db()
        self.assertEqual(step1.next_step, step2)

    def test_next_step_optional(self):
        step = self._make_step(order=1)
        self.assertIsNone(step.next_step)

    def test_config_default_empty(self):
        step = self._make_step()
        self.assertEqual(step.config, {})

    def test_config_stores_json(self):
        config = {"min": 0, "max": 100, "unit": "mg"}
        step = self._make_step(config=config)
        step.refresh_from_db()
        self.assertEqual(step.config["min"], 0)
        self.assertEqual(step.config["unit"], "mg")

    def test_str(self):
        step = self._make_step(order=1)
        self.assertIn("Passo 1", str(step))
        self.assertIn(str(self.version), str(step))

    def test_ordering(self):
        self._make_step(order=3)
        self._make_step(order=1)
        self._make_step(order=2)
        orders = list(
            ProtocolStep.objects.filter(
                version=self.version
            ).values_list("order", flat=True)
        )
        self.assertEqual(orders, [1, 2, 3])

    def test_cascade_delete_with_version(self):
        self._make_step(order=1)
        self.assertEqual(ProtocolStep.objects.count(), 1)
        self.version.delete()
        self.assertEqual(ProtocolStep.objects.count(), 0)


class ProtocolExecutionModelTest(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(title="Protocolo Execution Test")
        self.version = self.protocol.versions.first()
        self.physician = User.objects.create_user(
            username="medico_exec",
            email="medico_exec@test.com",
            password="testpass123",
            profile="medico",
        )

    def _make_execution(self, patient_name="João Silva", **kwargs):
        return ProtocolExecution.objects.create(
        version=self.version,
        physician=self.physician,
        patient_name=patient_name,
        **kwargs,
    )

    def test_create_execution(self):
        execution = self._make_execution()
        self.assertEqual(execution.status, ProtocolExecution.Status.EM_ANDAMENTO)
        self.assertIsNone(execution.current_step)
        self.assertIsNone(execution.finished_at)

    def test_status_choices(self):
        execution = self._make_execution()
        execution.status = ProtocolExecution.Status.CONCLUIDO
        execution.save()
        execution.refresh_from_db()
        self.assertEqual(execution.status, "concluido")

    def test_current_step_updates(self):
        step = ProtocolStep.objects.create(
            version=self.version,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=1,
            title="Passo 1",
        )
        execution = self._make_execution()
        execution.current_step = step
        execution.save()
        execution.refresh_from_db()
        self.assertEqual(execution.current_step, step)

    def test_str(self):
        execution = self._make_execution()
        self.assertIn("João Silva", str(execution))
        self.assertIn("Em andamento", str(execution))

    def test_multiple_executions_same_version(self):
        self._make_execution(patient_name="Paciente A")
        self._make_execution(patient_name="Paciente B")
        self.assertEqual(
            ProtocolExecution.objects.filter(
                version=self.version
            ).count(),
            2,
        )


class ProtocolExecutionStateModelTest(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(title="Protocolo State Test")
        self.version = self.protocol.versions.first()
        self.physician = User.objects.create_user(
            username="medico_state",
            email="medico_state@test.com",
            password="testpass123",
            profile="medico",
        )
        self.step = ProtocolStep.objects.create(
            version=self.version,
            step_type=ProtocolStep.StepType.INPUT_NUMERICO,
            order=1,
            title="Peso",
        )
        self.execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.physician,
            patient_name="Maria Silva",
        )

    def test_create_state(self):
        state = ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
            values={"value": 70.5},
        )
        self.assertEqual(state.loop_count, 0)
        self.assertEqual(state.values["value"], 70.5)

    def test_unique_state_per_step_execution(self):
        from django.db import IntegrityError
        ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
            values={"value": 70.5},
        )
        with self.assertRaises(IntegrityError):
            ProtocolExecutionState.objects.create(
                execution=self.execution,
                step=self.step,
                values={"value": 80.0},
            )

    def test_loop_count_increments(self):
        state = ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
            loop_count=3,
        )
        self.assertEqual(state.loop_count, 3)

    def test_values_default_empty(self):
        state = ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
        )
        self.assertEqual(state.values, {})

    def test_cascade_delete_with_execution(self):
        ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
        )
        self.assertEqual(ProtocolExecutionState.objects.count(), 1)
        self.execution.delete()
        self.assertEqual(ProtocolExecutionState.objects.count(), 0)

    def test_str(self):
        state = ProtocolExecutionState.objects.create(
            execution=self.execution,
            step=self.step,
        )
        self.assertIn("step", str(state))
        self.assertIn("1", str(state))
class EngineTest(TestCase):
    User=get_user_model()
    
    def setUp(self):
        #criando o usuario, o protocolo e seus passos p teste xd
        self.protocolo=Protocol.objects.create(
            title="Teste Protocol Engine",
            author="venicio!"
            )
        self.versao = self.protocolo.versions.first()
        

        self.medico = User.objects.create_user(
            username="medic_o",
            email="medico@gmail.com",
            password="testpass123",
            profile="medico"
        )
        self.exec = ProtocolExecution.objects.create(
            version=self.versao,
            physician=self.medico,
            patient_name="paciente"
        )

        self.passo2=ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=2,
            title="Segundo Passo"
            )
        
        self.passo1=ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=1,
            title="Primeiro Passo"
            )
        
        self.passo1.next_step = self.passo2
        self.passo1.save()


        self.engine = ProtocolExecutionEngine()
    
    def test_retorna_ou_nao_o_primeiro_step(self):
        first_step = self.engine.primeiro_step(self.versao)

        self.assertEqual(first_step, self.passo1)
    
    def test_primeiro_como_atual(self):
        exec = self.engine.comecar(self.exec)

        self.assertEqual(exec.current_step, self.passo1)
    
    def test_step_atual_salvando_estado(self):
        self.engine.comecar(self.exec)

        state=self.engine.resposta_step_atual(
            self.exec,
            {"confirmado": True}
        )

        self.assertEqual(state.execution, self.exec)
        self.assertEqual(state.step, self.passo1)
        self.assertEqual(state.values, {"confirmado": True})

    def test_step_atual_vai_p_proximo_step(self):
        self.engine.comecar(self.exec)

        self.engine.resposta_step_atual(
            self.exec,
            {"confirmado": True},
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, self.passo2)

    def test_conc_sem_next_step(self):
        self.engine.comecar(self.exec)
        # ir do passo 1 pro 2
        self.engine.resposta_step_atual(self.exec, {"confirmado": True})

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, self.passo2)

        # sem next step
        self.engine.resposta_step_atual(self.exec, {"finalizado": True})

        self.exec.refresh_from_db()
        self.assertIsNone(self.exec.current_step)
        self.assertEqual(self.exec.status, ProtocolExecution.Status.CONCLUIDO)
        self.assertIsNotNone(self.exec.finished_at)

    def test_answer_true_vai_p_true_next(self):
        step_true = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=3,
            title="caaminho true"
        )

        step_false = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=4,
            title="caminho false"
        )

        step_hipotetico= ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.SIM_NAO,
            order = 5,
            title=("step com pergunta"),
            config={
                "true_next_step_id": step_true.id,
                "false_next_step_id": step_false.id,
            }
        )

        self.exec.current_step = step_hipotetico
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"answer": True},
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, step_true)

    def test_answer_false_vai_p_false_next(self):
        step_true = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=3,
            title="caaminho true"
        )

        step_false = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=4,
            title="caminho false"
        )

        step_hipotetico= ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.SIM_NAO,
            order = 5,
            title=("step com pergunta"),
            config={
                "true_next_step_id": step_true.id,
                "false_next_step_id": step_false.id,
            }
        )

        self.exec.current_step = step_hipotetico
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"answer": False},
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, step_false)
    
    def test_checklist_com_minimo_vai_p_true(self):
        step_true = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.INFORMATIVO,
            order=6,
            title="checklist com minimo",
        )

        step_false = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.INFORMATIVO,
            order=7,
            title="checklist sem minimo",
        )

        step_hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.CHECKLIST,
            order=8,
            title="checklist",
            config={
                "min_checked": 2,
                "true_next_step_id": step_true.id,
                "false_next_step_id": step_false.id,
            },
        )

        self.exec.current_step = step_hipotetico
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"checked_items": ["s1", "s2"]}
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, step_true)

    def test_checklist_abaixo_do_minimo_vai_p_false(self):
        step_true = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.INFORMATIVO,
            order=6,
            title="checklist com minimo",
        )

        step_false = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.INFORMATIVO,
            order=7,
            title="checklist sem minimo",
        )

        step_hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.CHECKLIST,
            order=8,
            title="checklist",
            config={
                "min_checked": 2,
                "true_next_step_id": step_true.id,
                "false_next_step_id": step_false.id,
            },
        )

        self.exec.current_step = step_hipotetico
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"checked_items": ["s1"]}
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, step_false)
    
    def test_multipla_escolha(self):
        step_grave = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=20,
            title="caso grave"
        )
        step_leve = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=21,
            title="caso leve"
        )
        hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.MULTIPLA_ESCOLHA,
            order=22,
            title="deu p entender nesse ponto ne",
            config={
                "choices_next_step_ids":{
                    "grave": step_grave.id,
                    "leve": step_leve.id
                }
            }
        )

        self.exec.current_step=hipotetico
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"choice": "grave"},
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, step_grave)
        

    def test_titulacao_loop_abaixo_do_maximo_avanca_para_loop_next_step(self):
        loop_next = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=12,
            title="loop",
        )

        max_reached = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=13,
            title="maximo",
        )

        step_hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.LOOP_TITULACAO,
            order=14,
            title="titulacao",
            config={
                "max_iterations": 3,
                "loop_next_step_id": loop_next.id,
                "max_reached_next_step_id": max_reached.id,
            },
        )

        self.exec.current_step = step_hipotetico
        self.exec.save(update_fields=["current_step"])

        state = self.engine.resposta_step_atual(
            self.exec,
            {"dose_adjusted": True},
        )

        self.exec.refresh_from_db()
        state.refresh_from_db()

        self.assertEqual(state.loop_count, 1)
        self.assertEqual(self.exec.current_step, loop_next)

    def test_titulacao_loop_no_maximo_avanca_para_max_reached_next_step(self):
        loop_next = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=15,
            title="loop",
        )

        max_reached = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=16,
            title="maximo",
        )

        hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.LOOP_TITULACAO,
            order=17,
            title="Loop titulação",
            config={
                "max_iterations": 1,
                "loop_next_step_id": loop_next.id,
                "max_reached_next_step_id": max_reached.id,
            },
        )

        self.exec.current_step = hipotetico
        self.exec.save(update_fields=["current_step"])

        state = self.engine.resposta_step_atual(
            self.exec,
            {"dose_adjusted": True},
        )

        self.exec.refresh_from_db()
        state.refresh_from_db()

        self.assertEqual(state.loop_count, 1)
        self.assertEqual(self.exec.current_step, max_reached)

    def test_prescricao_salva_e_vai_p_next(self):
        next_step = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=23,
            title="proximo",
        )

        hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.PRESCRICAO,
            order=24,
            title="prescricao",
            next_step=next_step,
            config={
                "medications": [
                    {
                        "name": "SF 0,9%",
                        "dose": "20 ml/kg",
                        "route": "IV",
                    }
                ]
            },
        )
        self.exec.current_step = hipotetico
        self.exec.save(update_fields=["current_step"])

        state = self.engine.resposta_step_atual(
            self.exec,
            {"accepted": True},
        )

        self.exec.refresh_from_db()

        self.assertEqual(state.values, {"accepted": True})
        self.assertEqual(self.exec.current_step, next_step)

    def test_reav_salva_state_e_vai_p_next(self):
        next_step = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=25, title="reavaliacao"
        )
        hipotetico= ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.AGUARDAR_REAVALIAR,
            order=26,
            title="linguica p reavaliar",
            next_step=next_step,
            config={
                "duration_hours": 6,
                "reassess_fields": ["diurese", "pressao"]
            }
        )
        

        self.exec.current_step=hipotetico
        self.exec.save(update_fields=["current_step"])

        state= self.engine.resposta_step_atual(
            self.exec,
            {
                "diurese":"adequada",
                "pressao_arterial":"estavel"
            }
        )

        self.exec.refresh_from_db()

        self.assertEqual(state.values["diurese"], "adequada")
        self.assertEqual(self.exec.current_step, next_step)

    def test_input_numerico_salva_e_next(self):
        next_step= ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INFORMATIVO,
            order=27,
            title="pos peso",
        )

        numeric_step= ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INPUT_NUMERICO,
            order=28,
            title="peso",
            next_step=next_step,
            config={
                "field_name": "peso_kg",
                "unit": "kg",
                "min_value": 2,
                "max_value": 200
            }
        )
        self.exec.current_step = numeric_step
        self.exec.save(update_fields=["current_step"])

        state = self.engine.resposta_step_atual(
            self.exec,
            {"peso_kg": 12},
        )

        self.exec.refresh_from_db()

        self.assertEqual(state.values["peso_kg"], 12)
        self.assertEqual(self.exec.current_step, next_step)

    def test_calculadora_finalmente_mais_e_mult(self):
        result = self.engine.calcular_formula(
            "peso_kg * 10",
            {"peso_kg": 12}
        )

        self.assertEqual(result, 120)
        
    def test_variavel_desconhecida(self):
        with self.assertRaises(ValueError):
            self.engine.calcular_formula(
                "peso_kg * 10",
                {}
            )
    
    def test_derivado_calcula_e_salva_state(self):
        hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type= ProtocolStep.StepType.CALCULO_DERIVADO,
            order=18,
            title="calculo",
            config={
                "formula":"peso_kg * 10",
                "output_field": "volume_ml",
            }
        )

        self.exec.current_step = hipotetico
        self.exec.save(update_fields=["current_step"])

        state = self.engine.resposta_step_atual(
            self.exec,
            {"peso_kg": 12}
        )

        self.assertEqual(state.values["peso_kg"], 12)
        self.assertEqual(state.values["volume_ml"], 120)

    def test_derived_calc_usa_valor_de_step_anterior(self):
        peso_step = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.INPUT_NUMERICO,
            order=18,
            title="Peso",
        )

        hipotetico = ProtocolStep.objects.create(
            version=self.versao,
            step_type=ProtocolStep.StepType.CALCULO_DERIVADO,
            order=19,
            title="calcular ml",
            config={
                "formula": "peso_kg * 20",
                "output_field": "volume_ml",
            },
        )

        peso_step.next_step = hipotetico
        peso_step.save()

        self.exec.current_step = peso_step
        self.exec.save(update_fields=["current_step"])

        self.engine.resposta_step_atual(
            self.exec,
            {"peso_kg": 12},
        )

        self.exec.refresh_from_db()
        self.assertEqual(self.exec.current_step, hipotetico)

        state = self.engine.resposta_step_atual(
            self.exec,
            {},
        )

        self.assertEqual(state.values["volume_ml"], 240)


class GuidedProtocolInterpreterTest(TestCase):
    def test_get_first_step_id_from_steps_data(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {"id": "step_0", "type": "info", "title": "Intro"},
                {"id": "step_1", "type": "yes_no", "title": "Pergunta"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(interpreter.get_first_step_id(), "step_0")

    def test_get_step_from_dengue_fixture_json(self):
        import json
        from pathlib import Path

        from .engine.interpreter import GuidedProtocolInterpreter

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        steps_data = data[1]["fields"]["steps_data"]
        interpreter = GuidedProtocolInterpreter(steps_data)

        step = interpreter.get_step("step_c_avaliacao1")

        self.assertEqual(step["type"], "yes_no")
        self.assertEqual(step["true_next"], "step_c_manutencao")

    def test_resolve_next_step_linear_from_json(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "step_0",
                    "type": "info",
                    "title": "Intro",
                    "next_step": "step_1",
                },
                {"id": "step_1", "type": "info", "title": "Fim"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("step_0", {}),
            "step_1",
        )

    def test_resolve_yes_no_from_dengue_fixture_json(self):
        import json
        from pathlib import Path

        from .engine.interpreter import GuidedProtocolInterpreter

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        steps_data = data[1]["fields"]["steps_data"]
        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("step_c_avaliacao1", {"answer": True}),
            "step_c_manutencao",
        )
        self.assertEqual(
            interpreter.resolve_next_step_id("step_c_avaliacao1", {"answer": False}),
            "step_c_repeticao",
        )

    def test_resolve_checklist_from_dengue_fixture_json(self):
        import json
        from pathlib import Path

        from .engine.interpreter import GuidedProtocolInterpreter

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        steps_data = data[1]["fields"]["steps_data"]
        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id(
                "step_1_gravidade", {"checked_items": ["g1"]}
            ),
            "step_d_exames",
        )
        self.assertEqual(
            interpreter.resolve_next_step_id("step_1_gravidade", {"checked_items": []}),
            "step_1b_alerta",
        )

    def test_resolve_titration_loop_from_dengue_fixture_json(self):
        import json
        from pathlib import Path

        from .engine.interpreter import GuidedProtocolInterpreter

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        steps_data = data[1]["fields"]["steps_data"]
        interpreter = GuidedProtocolInterpreter(steps_data)

        # congestion=True → congestion_check.true_next
        self.assertEqual(
            interpreter.resolve_next_step_id(
                "step_c_repeticao",
                {"congestion": True},
                {"loop_count": 0},
            ),
            "step_c_avaliacao_horaria",
        )
        # Below max, no congestion → congestion_check.false_next
        self.assertEqual(
            interpreter.resolve_next_step_id(
                "step_c_repeticao",
                {"congestion": False},
                {"loop_count": 1},
            ),
            "step_c_avaliacao_horaria",
        )
        # At max iterations → max_reached_next
        self.assertEqual(
            interpreter.resolve_next_step_id(
                "step_c_repeticao",
                {"congestion": False},
                {"loop_count": 2},
            ),
            "step_c_avaliacao_horaria",
        )

    def test_resolve_multiple_choice_from_json(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "classificacao",
                    "type": "multiple_choice",
                    "title": "Classificacao",
                    "choices_next": {
                        "grave": "conduta_grave",
                        "leve": "conduta_leve",
                    },
                },
                {"id": "conduta_grave", "type": "info", "title": "Grave"},
                {"id": "conduta_leve", "type": "info", "title": "Leve"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("classificacao", {"choice": "grave"}),
            "conduta_grave",
        )

    def test_evaluate_formula_returns_decimal(self):
        from decimal import Decimal

        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})

        result = interpreter.evaluate_formula("peso_kg * 10", {"peso_kg": "12.5"})

        self.assertEqual(result, Decimal("125.0"))

    def test_evaluate_formula_rejects_unknown_variable(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})

        with self.assertRaises(ValueError):
            interpreter.evaluate_formula("peso_kg * 10", {})

    def test_apply_derived_calculation_from_json(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "calc_volume",
                    "type": "derived_calc",
                    "title": "Volume",
                    "formula": "peso_kg * 10",
                    "output_field": "volume_ml",
                }
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        values = interpreter.apply_derived_calculation(
            "calc_volume",
            {"peso_kg": "12"},
        )

        self.assertEqual(values["peso_kg"], "12")
        self.assertEqual(values["volume_ml"], "120")

    def test_apply_derived_calculation_uses_previous_context(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "calc_volume",
                    "type": "derived_calc",
                    "title": "Volume",
                    "formula": "peso_kg * 20",
                    "output_field": "volume_ml",
                }
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        values = interpreter.apply_derived_calculation(
            "calc_volume",
            {},
            {"peso_kg": "12"},
        )

        self.assertEqual(values["volume_ml"], "240")

    def test_build_context_from_json_history(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})
        history = [
            {
                "step_key": "step_peso",
                "values": {"peso_kg": "12"},
            },
            {
                "step_key": "step_ht",
                "values": {"hematocrito": "40"},
            },
        ]

        context = interpreter.build_context(
            history,
            {"peso_kg": "13"},
        )

        self.assertEqual(context["peso_kg"], "13")
        self.assertEqual(context["hematocrito"], "40")

    def test_resolve_numeric_input_next_step(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "peso",
                    "type": "numeric_input",
                    "title": "Peso",
                    "field_name": "peso_kg",
                    "next_step": "volume",
                },
                {"id": "volume", "type": "info", "title": "Volume"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("peso", {"peso_kg": 70}),
            "volume",
        )

    def test_resolve_medication_prescription_next_step(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "prescricao",
                    "type": "medication_prescription",
                    "title": "Prescricao",
                    "medications": [{"name": "SF", "dose": "10 ml/kg", "route": "IV"}],
                    "next_step": "fim",
                },
                {"id": "fim", "type": "info", "title": "Fim"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("prescricao", {"accepted": True}),
            "fim",
        )

    def test_resolve_wait_reassess_next_step(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "reavaliacao",
                    "type": "wait_reassess",
                    "title": "Reavaliacao",
                    "duration_hours": 6,
                    "reassess_fields": ["diurese"],
                    "next_step": "fim",
                },
                {"id": "fim", "type": "info", "title": "Fim"},
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        self.assertEqual(
            interpreter.resolve_next_step_id("reavaliacao", {"diurese": "adequada"}),
            "fim",
        )

    def test_evaluate_gate_passes(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})
        gate = {
            "expression": "peso_kg > 10",
            "level": "warning",
            "message": "Peso baixo",
        }

        result = interpreter.evaluate_gate(gate, {"peso_kg": 12})

        self.assertIsNone(result)

    def test_evaluate_gate_fails(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})
        gate = {
            "expression": "peso_kg > 10",
            "level": "warning",
            "message": "Peso baixo",
        }

        result = interpreter.evaluate_gate(gate, {"peso_kg": 5})

        self.assertIsNotNone(result)
        self.assertFalse(result["passed"])
        self.assertEqual(result["level"], "warning")

    def test_evaluate_step_gates_with_multiple_gates(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {
                    "id": "step_gates",
                    "type": "info",
                    "title": "Step com gates",
                    "gate": [
                        {
                            "expression": "peso_kg > 10",
                            "level": "warning",
                            "message": "Peso baixo",
                        },
                        {
                            "expression": "peso_kg < 200",
                            "level": "critical",
                            "message": "Peso alto",
                        },
                    ],
                    "next_step": None,
                },
            ]
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        # Both pass
        warnings = interpreter.evaluate_step_gates("step_gates", {"peso_kg": 50})
        self.assertEqual(len(warnings), 0)

        # First fails (5 > 10 is False)
        warnings = interpreter.evaluate_step_gates("step_gates", {"peso_kg": 5})
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["level"], "warning")

    def test_evaluate_entry_gates(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        steps_data = {
            "steps": [
                {"id": "intro", "type": "info", "title": "Intro"},
            ],
            "entry_gates": [
                {
                    "expression": "peso_kg > 10",
                    "failure_message": "Peso muito baixo",
                },
            ],
        }

        interpreter = GuidedProtocolInterpreter(steps_data)

        # Passes
        warnings = interpreter.evaluate_entry_gates({"peso_kg": 12})
        self.assertEqual(len(warnings), 0)

        # Fails
        warnings = interpreter.evaluate_entry_gates({"peso_kg": 5})
        self.assertEqual(len(warnings), 1)

    def test_evaluate_boolean_expression_with_and_or(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})
        gate_and = {
            "expression": "peso_kg > 10 and peso_kg < 100",
            "level": "warning",
            "message": "",
        }
        gate_or = {
            "expression": "peso_kg < 5 or peso_kg > 100",
            "level": "warning",
            "message": "",
        }

        # and: both true → passes
        self.assertIsNone(interpreter.evaluate_gate(gate_and, {"peso_kg": 50}))
        # and: one false → fails
        self.assertIsNotNone(interpreter.evaluate_gate(gate_and, {"peso_kg": 5}))
        # or: both false → fails
        self.assertIsNotNone(interpreter.evaluate_gate(gate_or, {"peso_kg": 50}))
        # or: one true → passes
        self.assertIsNone(interpreter.evaluate_gate(gate_or, {"peso_kg": 150}))

    def test_evaluate_boolean_expression_with_in(self):
        from .engine.interpreter import GuidedProtocolInterpreter

        interpreter = GuidedProtocolInterpreter({"steps": []})
        gate = {"expression": "'febre' in sintomas", "level": "warning", "message": ""}

        # Present → passes
        self.assertIsNone(
            interpreter.evaluate_gate(
                gate, {"sintomas": ["febre", "vomito"]}
            )
        )
        # Absent → fails
        self.assertIsNotNone(interpreter.evaluate_gate(gate, {"sintomas": ["vomito"]}))


class JsonProtocolExecutionServiceTest(TestCase):
    def setUp(self):
        self.protocol = Protocol.objects.create(title="JSON Protocol")
        self.version = self.protocol.versions.first()
        self.version.steps_data = {
            "steps": [
                {
                    "id": "intro",
                    "type": "info",
                    "title": "Intro",
                    "next_step": "pergunta",
                },
                {
                    "id": "pergunta",
                    "type": "yes_no",
                    "title": "Pergunta",
                    "true_next": "fim_sim",
                    "false_next": "fim_nao",
                },
                {
                    "id": "fim_sim",
                    "type": "info",
                    "title": "Fim sim",
                    "next_step": "checklist",
                },
                {
                    "id": "fim_nao",
                    "type": "info",
                    "title": "Fim nao",
                    "next_step": None,
                },
                {
                    "id": "checklist",
                    "type": "checklist",
                    "title": "Checklist",
                    "items": [
                        {"id": "c1", "label": "Item 1"},
                        {"id": "c2", "label": "Item 2"},
                    ],
                    "rule": {
                        "min_checked": 1,
                        "true_next": "multiple_choice",
                        "false_next": "multiple_choice",
                    },
                },
                {
                    "id": "multiple_choice",
                    "type": "multiple_choice",
                    "title": "Multipla escolha",
                    "choices_next": {"a": "numeric", "b": "numeric"},
                },
                {
                    "id": "numeric",
                    "type": "numeric_input",
                    "title": "Peso",
                    "field_name": "peso_kg",
                    "unit": "kg",
                    "min_value": 2,
                    "max_value": 200,
                    "next_step": "derived_calc",
                },
                {
                    "id": "derived_calc",
                    "type": "derived_calc",
                    "title": "Volume",
                    "inputs": ["peso_kg"],
                    "formula": "peso_kg * 10",
                    "output_label": "volume_ml",
                    "next_step": "medication",
                },
                {
                    "id": "medication",
                    "type": "medication_prescription",
                    "title": "Prescricao",
                    "medications": [{"name": "SF", "dose": "10 ml/kg", "route": "IV"}],
                    "next_step": "wait_reassess",
                },
                {
                    "id": "wait_reassess",
                    "type": "wait_reassess",
                    "title": "Reavaliacao",
                    "duration_hours": 6,
                    "reassess_fields": ["diurese"],
                    "next_step": "titration",
                },
                {
                    "id": "titration",
                    "type": "titration_loop",
                    "title": "Titulacao",
                    "max_iterations": 3,
                    "counter_field": "dose_count",
                    "congestion_check": {
                        "title": "Congestao?",
                        "true_next": "fim_total",
                        "false_next": "fim_total",
                    },
                    "max_reached_next": "fim_total",
                },
                {
                    "id": "fim_total",
                    "type": "info",
                    "title": "Fim total",
                    "next_step": None,
                },
            ]
        }
        self.version.save()
        self.physician = User.objects.create_user(
            username="json_doctor",
            email="json_doctor@test.com",
            password="testpass123",
            profile="medico",
        )
        self.execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.physician,
            patient_name="Paciente JSON",
        )
        self.engine = ProtocolExecutionEngine()

    def test_start_execution_uses_first_json_step_key(self):
        execution = self.engine.comecar(self.execution)

        self.assertEqual(execution.current_step_key, "intro")
        self.assertIsNone(execution.current_step)

    def test_answer_json_step_persists_state_and_advances_by_step_key(self):
        self.engine.comecar(self.execution)

        state = self.engine.resposta_step_atual(
            self.execution,
            {"ack": True},
        )

        self.execution.refresh_from_db()

        self.assertEqual(state.step_key, "intro")
        self.assertIsNone(state.step)
        self.assertEqual(state.values, {"ack": True})
        self.assertEqual(self.execution.current_step_key, "pergunta")

    def test_answer_json_yes_no_advances_to_true_next(self):
        self.engine.comecar(self.execution)
        self.engine.resposta_step_atual(self.execution, {"ack": True})
        self.execution.refresh_from_db()

        self.engine.resposta_step_atual(self.execution, {"answer": True})
        self.execution.refresh_from_db()

        self.assertEqual(self.execution.current_step_key, "fim_sim")

    def test_start_with_context_evaluates_entry_gates(self):
        self.version.steps_data = {
            "steps": [
                {"id": "intro", "type": "info", "title": "Intro", "next_step": None},
            ],
            "entry_gates": [
                {
                    "expression": "sintomas == 'febre'",
                    "failure_message": "Paciente sem febre",
                },
            ],
        }
        self.version.save()

        execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.physician,
            patient_name="Teste Gates",
        )

        execution = self.engine.comecar(execution, {"sintomas": "dor"})
        execution.refresh_from_db()

        state = execution.states.first()
        self.assertTrue(len(state.gate_warnings) > 0)

    def test_start_with_step_gate_warning(self):
        self.version.steps_data = {
            "steps": [
                {
                    "id": "intro",
                    "type": "info",
                    "title": "Intro",
                    "gate": {
                        "expression": "peso_kg > 10",
                        "level": "warning",
                        "message": "Peso muito baixo",
                    },
                    "next_step": None,
                },
            ],
        }
        self.version.save()

        execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.physician,
            patient_name="Teste Gate Step",
        )

        execution = self.engine.comecar(execution, {"peso_kg": 5})
        execution.refresh_from_db()

        state = execution.states.first()
        self.assertTrue(len(state.gate_warnings) > 0)

    def test_answer_checklist_advances(self):
        self.engine.comecar(self.execution)
        self.engine.resposta_step_atual(self.execution, {"ack": True})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "pergunta")

        self.engine.resposta_step_atual(self.execution, {"answer": True})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "fim_sim")

        self.engine.resposta_step_atual(self.execution, {"ack": True})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "checklist")

        self.engine.resposta_step_atual(self.execution, {"checked_items": ["c1"]})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "multiple_choice")

    def test_answer_multiple_choice_advances(self):
        self.execution.current_step_key = "multiple_choice"
        self.execution.save(update_fields=["current_step_key"])

        self.engine.resposta_step_atual(self.execution, {"choice": "a"})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "numeric")

    def test_answer_titration_loop_increments_counter(self):
        self.execution.current_step_key = "titration"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"congestion": False})
        state.refresh_from_db()

        self.assertEqual(state.loop_count, 1)
        self.assertEqual(self.execution.current_step_key, "fim_total")

    def test_answer_numeric_input_saves_value(self):
        self.execution.current_step_key = "numeric"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"peso_kg": 70})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["peso_kg"], 70)
        self.assertEqual(self.execution.current_step_key, "derived_calc")

    def test_answer_medication_prescription_saves(self):
        self.execution.current_step_key = "medication"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"accepted": True})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["accepted"], True)
        self.assertEqual(self.execution.current_step_key, "wait_reassess")

    def test_answer_wait_reassess_saves(self):
        self.execution.current_step_key = "wait_reassess"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"diurese": "adequada"})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["diurese"], "adequada")
        self.assertEqual(self.execution.current_step_key, "titration")

    def test_answer_derived_calc_calculates(self):
        self.execution.current_step_key = "derived_calc"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"peso_kg": "12"})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["volume_ml"], "120")
        self.assertEqual(self.execution.current_step_key, "medication")

    def test_avancar_step_advances_without_answer(self):
        self.execution.current_step_key = "intro"
        self.execution.save(update_fields=["current_step_key"])

        self.engine.avancar_step(self.execution)
        self.execution.refresh_from_db()

        self.assertEqual(self.execution.current_step_key, "pergunta")

    def test_avancar_step_concludes_when_no_next(self):
        self.execution.current_step_key = "fim_nao"
        self.execution.save(update_fields=["current_step_key"])

        self.engine.avancar_step(self.execution)
        self.execution.refresh_from_db()

        self.assertIsNone(self.execution.current_step_key)
        self.assertEqual(self.execution.status, ProtocolExecution.Status.CONCLUIDO)

    def test_get_reminders_returns_wait_reassess(self):
        self.execution.current_step_key = "wait_reassess"
        self.execution.save(update_fields=["current_step_key"])

        self.engine.resposta_step_atual(self.execution, {"diurese": "adequada"})
        self.execution.refresh_from_db()

        reminders = self.engine.get_reminders(self.execution)
        self.assertEqual(len(reminders), 1)
        self.assertIn("due_at", reminders[0])
        self.assertIn("status", reminders[0])


class JsonProtocolExecutionApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.protocol = Protocol.objects.create(title="JSON API Protocol")
        self.version = self.protocol.versions.first()
        self.version.steps_data = {
            "steps": [
                {
                    "id": "intro",
                    "type": "info",
                    "title": "Intro",
                    "next_step": "pergunta",
                },
                {
                    "id": "pergunta",
                    "type": "yes_no",
                    "title": "Pergunta",
                    "true_next": "fim_sim",
                    "false_next": "fim_nao",
                },
                {"id": "fim_sim", "type": "info", "title": "Fim sim"},
                {"id": "fim_nao", "type": "info", "title": "Fim nao"},
            ]
        }
        self.version.save()
        self.doctor = User.objects.create_user(
            username="json_api_doctor",
            email="json_api_doctor@test.com",
            password="testpass123",
            profile="medico",
        )

    def test_execute_start_returns_step_data(self):
        self.client.force_authenticate(user=self.doctor)

        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente API JSON"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["current_step_key"], "intro")
        self.assertEqual(response.data["current_step_data"]["id"], "intro")
        self.assertEqual(response.data["current_step_data"]["type"], "info")

    def test_execute_answer_returns_next_step_data(self):
        self.client.force_authenticate(user=self.doctor)

        self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente API JSON"},
            format="json",
        )

        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/answer/",
            {"values": {"ack": True}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_step_key"], "pergunta")
        self.assertEqual(response.data["current_step_data"]["id"], "pergunta")
        self.assertEqual(response.data["current_step_data"]["type"], "yes_no")

    def test_execute_start_idempotent(self):
        self.client.force_authenticate(user=self.doctor)
        client_uuid = str(uuid4())

        first_response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {
                "patient_name": "Paciente API JSON",
                "client_uuid": client_uuid,
            },
            format="json",
        )
        second_response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {
                "patient_name": "Paciente API JSON",
                "client_uuid": client_uuid,
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(first_response.data["id"], second_response.data["id"])
        self.assertEqual(
            ProtocolExecution.objects.filter(client_uuid=client_uuid).count(),
            1,
        )


class ProtocolExecuteApiTest(TestCase):
    def setUp(self):
        import json
        from pathlib import Path

        self.client = APIClient()

        fixture_path = Path(__file__).parent / "fixtures" / "dengue_guiado.json"
        with open(fixture_path) as f:
            data = json.load(f)

        self.steps_data = data[1]["fields"]["steps_data"]
        self.protocol = Protocol.objects.create(title="Dengue JSON Runtime")
        self.version = self.protocol.versions.first()
        self.version.steps_data = self.steps_data
        self.version.save()
        self.doctor = User.objects.create_user(
            username="exec_doctor",
            email="exec_doctor@test.com",
            password="testpass123",
            profile="medico",
        )
        self.execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.doctor,
            patient_name="Paciente Dengue",
        )
        self.engine = ProtocolExecutionEngine()

    def test_execute_start(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente Test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["current_step_key"], "step_0")
        self.assertIn("gate_warnings", response.data)

    def test_execute_start_idempotent(self):
        self.client.force_authenticate(user=self.doctor)
        client_uuid = str(uuid4())
        r1 = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente", "client_uuid": client_uuid},
            format="json",
        )
        r2 = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente", "client_uuid": client_uuid},
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.data["id"], r2.data["id"])

    def test_execute_step(self):
        self.client.force_authenticate(user=self.doctor)
        self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente"},
            format="json",
        )
        response = self.client.get(
            f"/api/v1/protocols/{self.protocol.pk}/execute/step/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("step", response.data)
        self.assertIn("gate_warnings", response.data)
        self.assertEqual(response.data["step"]["id"], "step_0")

    def test_execute_answer(self):
        self.client.force_authenticate(user=self.doctor)
        self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente"},
            format="json",
        )
        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/answer/",
            {"values": {"ack": True}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_step_key"], "step_1_gravidade")

    def test_execute_next(self):
        self.client.force_authenticate(user=self.doctor)
        self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente"},
            format="json",
        )
        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/next/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("step", response.data)
        self.assertEqual(response.data["step"]["id"], "step_1_gravidade")

    def test_execute_reminders(self):
        self.client.force_authenticate(user=self.doctor)
        # Use execution from setUp, set it to wait_reassess step
        self.execution.current_step_key = "step_c_avaliacao_horaria"
        self.execution.save(update_fields=["current_step_key"])
        # Answer wait_reassess
        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/answer/",
            {"values": {"diurese": "adequada"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            f"/api/v1/protocols/{self.protocol.pk}/execute/reminders/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reminders", response.data)
        self.assertEqual(len(response.data["reminders"]), 1)

    def test_execute_start_with_context(self):
        self.client.force_authenticate(user=self.doctor)
        response = self.client.post(
            f"/api/v1/protocols/{self.protocol.pk}/execute/",
            {"patient_name": "Paciente", "context": {"sintomas": ["febre"]}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["id"])

    def test_dengue_runtime_starts_from_fixture_first_step(self):
        self.engine.comecar(self.execution)

        self.execution.refresh_from_db()

        self.assertEqual(self.execution.current_step_key, "step_0")
        self.assertIsNone(self.execution.current_step)

    def test_dengue_runtime_checklist_gravity_to_exams(self):
        self.engine.comecar(self.execution)
        self.engine.resposta_step_atual(self.execution, {"ack": True})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "step_1_gravidade")

        state = self.engine.resposta_step_atual(
            self.execution,
            {"checked_items": ["g1"]},
        )
        self.execution.refresh_from_db()

        self.assertEqual(state.step_key, "step_1_gravidade")
        self.assertEqual(self.execution.current_step_key, "step_d_exames")

    def test_dengue_runtime_yes_no_expansao_to_manutencao(self):
        self.execution.current_step_key = "step_c_avaliacao1"
        self.execution.save(update_fields=["current_step_key"])

        self.engine.resposta_step_atual(self.execution, {"answer": True})
        self.execution.refresh_from_db()

        self.assertEqual(self.execution.current_step_key, "step_c_manutencao")

    def test_dengue_runtime_checklist_alert_to_outside(self):
        self.engine.comecar(self.execution)
        self.engine.resposta_step_atual(self.execution, {"ack": True})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "step_1_gravidade")

        self.engine.resposta_step_atual(self.execution, {"checked_items": []})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "step_1b_alerta")

        self.engine.resposta_step_atual(self.execution, {"checked_items": []})
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.current_step_key, "step_fora_protocolo")

    def test_dengue_runtime_numeric_input_saves_peso(self):
        self.execution.current_step_key = "step_c_peso"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"peso_kg": 70})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["peso_kg"], 70)
        self.assertEqual(self.execution.current_step_key, "step_c_expansao")

    def test_dengue_runtime_derived_calc_calculates_volume(self):
        self.execution.current_step_key = "step_c_expansao"
        self.execution.save(update_fields=["current_step_key"])

        state = self.engine.resposta_step_atual(self.execution, {"peso_kg": "12"})
        self.execution.refresh_from_db()

        self.assertEqual(state.values["Volume de SF 0,9% por bolus"], "120")

    def test_dengue_runtime_starts_with_context(self):
        execution = ProtocolExecution.objects.create(
            version=self.version,
            physician=self.doctor,
            patient_name="Paciente Com Contexto",
        )
        execution = self.engine.comecar(execution, {"sintomas": ["febre"]})
        execution.refresh_from_db()

        state = execution.states.first()
        self.assertEqual(state.values, {"sintomas": ["febre"]})
        self.assertEqual(state.gate_warnings, [])
        
