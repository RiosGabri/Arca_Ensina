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
