from rest_framework import viewsets

from .models import Paciente, Sintoma
from .serializers import PacienteSerializer, SintomaSerializer


class PacienteViewSet(viewsets.ModelViewSet):
    serializer_class = PacienteSerializer
    pagination_class = None

    def get_queryset(self):
        # Cada médico só enxerga os pacientes que ele mesmo cadastrou.
        return Paciente.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SintomaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sintoma.objects.all()
    serializer_class = SintomaSerializer
    pagination_class = None
