from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class InicioViewTests(TestCase):
    def test_inicio_renderiza_para_usuario_autenticado(self):
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Centro de control')
        self.assertContains(response, 'Abrir dashboard')

# Create your tests here.
