from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Paciente

User = get_user_model()


class PacienteLogicTest(TestCase):
    def setUp(self):
        Paciente.objects.create(
            nome="Rios Teste",
            data_nascimento="2000-01-01",
            telefone="5581999999999",
            peso=80.5,
            genero="M",
            cidade="Recife",
        )

    def test_paciente_dados_corretos(self):
        p = Paciente.objects.get(nome="Rios Teste")
        self.assertEqual(float(p.weight if hasattr(p, "weight") else p.peso), 80.5)


class PacienteAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testerios@test.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_pacientes_list(self):
        url = reverse("paciente-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_only_own_patients(self):
        outro_medico = User.objects.create_user(
            email="outro@test.com", password="password123"
        )
        Paciente.objects.create(
            nome="Paciente do Outro",
            data_nascimento="2010-01-01",
            telefone="5581988888888",
            genero="M",
            cidade="Recife",
            created_by=outro_medico,
        )
        meu_paciente = Paciente.objects.create(
            nome="Meu Paciente",
            data_nascimento="2012-01-01",
            telefone="5581977777777",
            genero="F",
            cidade="Recife",
            created_by=self.user,
        )

        url = reverse("paciente-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p["id"] for p in response.data]
        self.assertEqual(ids, [meu_paciente.id])

    def test_create_sets_created_by(self):
        url = reverse("paciente-list", kwargs={"version": "v1"})
        response = self.client.post(
            url,
            {
                "nome": "Novo Paciente",
                "data_nascimento": "2015-06-01",
                "telefone": "5581966666666",
                "genero": "M",
                "cidade": "Recife",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        paciente = Paciente.objects.get(id=response.data["id"])
        self.assertEqual(paciente.created_by, self.user)
