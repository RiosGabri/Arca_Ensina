from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.calculator import services
from apps.medications.models import Medication


class CalculatorServiceTests(TestCase):
    def test_calculate_dosage_mg(self):
        # calcular dosagem com peso e prescrição apenas:
        pacient_weight = 15  # kg
        medication_prescription = 50  # mg/kg
        dosage = services.calculate_dosage_mg(medication_prescription, pacient_weight)
        # 50 mg/kg * 15 kg = 750 mg
        self.assertEqual(dosage, Decimal("750.00"))

        pacient_weight = 20  # kg
        medication_prescription = 25  # mg/kg
        dosage = services.calculate_dosage_mg(medication_prescription, pacient_weight)
        # 25 mg/kg * 20 kg = 500 mg
        self.assertEqual(dosage, Decimal("500.00"))

        # calcular dosagem com peso, altura e prescrição por m2:
        pacient_weight = 15  # kg
        pacient_height = 80  # cm
        medication_prescription = 100  # mg/m2
        dosage = services.calculate_dosage_mg(
            medication_prescription, pacient_weight, pacient_height
        )
        # Superfície corporal = sqrt((15*80)/3600) = 0.577 m2
        # Dosagem = 100 mg/m2 * 0.577 m2 = 57.7 mg
        self.assertEqual(dosage, Decimal("57.74"))

        pacient_weight = 20  # kg
        pacient_height = 100  # cm
        medication_prescription = 50  # mg/m2
        dosage = services.calculate_dosage_mg(
            medication_prescription, pacient_weight, pacient_height
        )
        self.assertEqual(dosage, Decimal("37.27"))

    def test_calculate_dosage_mg_invalid_values(self):
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(50, -5)  # peso negativo
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(70, 0)  # peso zero
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(50, 15, 0)  # altura zero
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(50, 15, -80)  # altura negativa
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(-50, 15)  # prescrição negativa
        with self.assertRaises(ValueError):
            services.calculate_dosage_mg(0, 15)  # prescrição zero

    def test_prescription_to_frequency(self):
        # a cada 8 horas = 3 vezes ao dia
        self.assertEqual(services.prescription_to_frequency(8), 3)
        # a cada 6 horas = 4 vezes ao dia
        self.assertEqual(services.prescription_to_frequency(6), 4)
        # a cada 12 horas = 2 vezes ao dia
        self.assertEqual(services.prescription_to_frequency(12), 2)
        # a cada 24 horas = 1 vez ao dia
        self.assertEqual(services.prescription_to_frequency(24), 1)

    def test_calculate_dosage_per_dose(self):
        # 750 mg por dia dividido em 3 doses = 250 mg por dose
        self.assertEqual(
            services.calculate_dosage_per_dose(750, 3),
            Decimal("250.00"),
        )
        # 1200 mg por dia dividido em 4 doses = 300 mg por dose
        self.assertEqual(
            services.calculate_dosage_per_dose(1200, 4),
            Decimal("300.00"),
        )

    def test_dosage_to_ml_conversion(self):
        # 250 mg / (50 mg/5 ml) = 25 ml
        self.assertEqual(
            services.convert_dosage_to_ml(250, 50, 5),
            Decimal("25.00"),
        )
        # 300 mg / (100 mg/10 ml) = 30 ml
        self.assertEqual(
            services.convert_dosage_to_ml(300, 100, 10),
            Decimal("30.00"),
        )


class CalculatorViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # usuário médico
        self.user = User.objects.create_user(
            email="doctor@test.com",
            password="strongpass123",
            profile="medico",
        )

        # autentica
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "doctor@test.com", "password": "strongpass123"},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        # medicamento de teste
        self.medication = Medication.objects.create(
            name="Amoxicilina",
            prescription=50,
            frequency_hours=8,
            min_dose_mg_kg=25,
            max_dose_mg_kg=90,
            max_absolute_dose_mg=3000,
            concentration_mg=250,
            concentration_ml=5,
            limits_by_age=None,
        )

    def test_calculator_valid_input(self):
        response = self.client.post(
            "/api/v1/calculator/calculate/",
            {"weight": 15, "age_days": 365, "medication_id": self.medication.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("dosage_mg", response.data)
        self.assertIn("dosage_per_dose", response.data)
        self.assertIn("frequency_per_day", response.data)
        self.assertIn("volume_ml", response.data)
        self.assertIn("warnings", response.data)

    def test_calculator_missing_weight(self):
        response = self.client.post(
            "/api/v1/calculator/calculate/",
            {"age_days": 365, "medication_id": self.medication.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        print(f"Response data: {response.data}")
        self.assertIn("weight", response.data)

    def test_calculator_invalid_medication_id(self):
        response = self.client.post(
            "/api/v1/calculator/calculate/",
            {
                "weight": 15,
                "age_days": 365,
                # ID de medicamento inexistente
                "medication_id": 9999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("medication_id", response.data)

    def test_calculator_no_medication_id(self):
        response = self.client.post(
            "/api/v1/calculator/calculate/",
            {"weight": 15, "age_days": 365},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("medication_id", response.data)

    def test_calculator_requires_auth(self):
        self.client.credentials()  # remove o token
        response = self.client.post(
            "/api/v1/calculator/calculate/",
            {"weight": 15, "medication_id": self.medication.id},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class CalculatorValidationTests(TestCase):
    def test_dosage_below_minimum(self):
        dosage = 300  # mg/kg
        weight = 15  # kg
        min_dose_mg_kg = 25
        max_dose_mg_kg = 300
        max_absolute_dose_mg = 2500

        warning, dosage_per_dose = services.validate_dosage(
            dosage,
            weight,
            min_dose_mg_kg,
            max_dose_mg_kg,
            max_absolute_dose_mg,
        )
        self.assertIn("BAIXO", warning)

    def test_dosage_above_maximum(self):
        dosage = 1500  # mg/kg
        weight = 15  # kg
        min_dose_mg_kg = 25
        max_dose_mg_kg = 90
        max_absolute_dose_mg = 3000

        warning, dosage_per_dose = services.validate_dosage(
            dosage,
            weight,
            min_dose_mg_kg,
            max_dose_mg_kg,
            max_absolute_dose_mg,
        )
        self.assertIn("ALTO", warning)

    def test_dosage_above_absolute_maximum(self):
        dosage = 3000  # mg
        weight = 15  # kg
        min_dose_mg_kg = 25
        max_dose_mg_kg = 90
        max_absolute_dose_mg = 2500

        warning, dosage_per_dose = services.validate_dosage(
            dosage,
            weight,
            min_dose_mg_kg,
            max_dose_mg_kg,
            max_absolute_dose_mg,
        )
        self.assertIn("CRITICO", warning)

    def test_dosage_inside_limits(self):
        dosage = 750  # mg/kg
        weight = 15  # kg
        min_dose_mg_kg = 25
        max_dose_mg_kg = 90
        max_absolute_dose_mg = 3000

        warning, dosage_per_dose = services.validate_dosage(
            dosage,
            weight,
            min_dose_mg_kg,
            max_dose_mg_kg,
            max_absolute_dose_mg,
        )
        self.assertEqual(warning, [])

    def test_dosage_per_age_validation(self):
        dosage = 900  # mg/kg
        weight = 15  # kg
        age_days = 200  # dias
        limits = {
            "neonatal": {"min": 20, "max": 40, "absolute_max": 1000},
            "lactente": {"min": 25, "max": 50, "absolute_max": 1500},
            "crianca": {"min": 30, "max": 60, "absolute_max": 2000},
            "adolescente": {"min": 35, "max": 70, "absolute_max": 2500},
            "adulto": {"min": 25, "max": 90, "absolute_max": 3000},
        }

        warning, dosage_per_dose = services.validate_dosage_per_age(
            dosage, age_days, limits, weight
        )
        self.assertIn("ALTO", warning)
