from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from empleados.models import Empleado, GerenciaArea
from licencias.models import Asignacion, Empresa, Licencia, Tenant, TipoLicencia
from licencias.services.asignacion import (
    asignar_licencia as svc_asignar,
    liberar_licencia as svc_liberar,
)
from licencias.services.exceptions import (
    AsignacionInactivaError,
    EmpleadoYaTieneTipoError,
)


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


class AsignacionServiceTests(TestCase):
    """Tests del service de asignación/liberación, no de las vistas."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.factory = RequestFactory()

        self.tenant = Tenant.objects.create(nombre='Tenant Test')
        self.empresa = Empresa.objects.create(tenant=self.tenant, nombre='Empresa Test')
        self.area = GerenciaArea.objects.create(
            empresa=self.empresa, codigo='GTI', nombre='Tecnología',
        )
        self.empleado = Empleado.objects.create(
            nombre_completo='Juan Pérez',
            ci='12345678',
            email_principal='juan@example.com',
            empresa=self.empresa,
            area=self.area,
        )
        self.tipo = TipoLicencia.objects.create(nombre='Office 365 E3')
        self.licencia = Licencia.objects.create(
            tenant=self.tenant,
            empresa=self.empresa,
            tipo=self.tipo,
            fecha_compra=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=365),
        )

    def _request(self):
        request = self.factory.post('/dummy/')
        request.user = self.user
        return request

    def test_asignar_licencia_crea_asignacion_activa(self):
        asignacion = svc_asignar(self.licencia.id, self.empleado.id, self._request())

        self.assertTrue(asignacion.activo)
        self.assertIsNotNone(asignacion.fecha_asignacion)
        self.assertEqual(asignacion.area_snapshot, 'GTI')
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_asignar_licencia_falla_si_empleado_ya_tiene_ese_tipo(self):
        otra_licencia = Licencia.objects.create(
            tenant=self.tenant,
            empresa=self.empresa,
            tipo=self.tipo,
            fecha_compra=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=365),
        )
        svc_asignar(self.licencia.id, self.empleado.id, self._request())

        with self.assertRaises(EmpleadoYaTieneTipoError) as ctx:
            svc_asignar(otra_licencia.id, self.empleado.id, self._request())

        self.assertEqual(ctx.exception.empleado_nombre, 'Juan Pérez')
        self.assertEqual(ctx.exception.tipo_nombre, 'Office 365 E3')
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_liberar_licencia_marca_inactiva_y_setea_fecha_retiro(self):
        asignacion = svc_asignar(self.licencia.id, self.empleado.id, self._request())

        svc_liberar(asignacion.id, 'Devolución', self._request())

        asignacion.refresh_from_db()
        self.assertFalse(asignacion.activo)
        self.assertIsNotNone(asignacion.fecha_retiro)
        self.assertEqual(asignacion.observaciones, 'Devolución')

        with self.assertRaises(AsignacionInactivaError):
            svc_liberar(asignacion.id, '', self._request())
