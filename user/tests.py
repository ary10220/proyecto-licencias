from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse


class UserPermissionActionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.operator = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='operatorpass123'
        )
        self.target = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='targetpass123',
            is_active=True
        )

    def test_toggle_usuario_get_does_not_change_user(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('toggle_usuario', args=[self.target.id]))

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.target.is_active)

    def test_toggle_usuario_without_permission_does_not_change_user(self):
        self.client.force_login(self.operator)

        response = self.client.post(reverse('toggle_usuario', args=[self.target.id]))

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/accounts/login/', response['Location'])
        self.assertTrue(self.target.is_active)

    def test_toggle_usuario_with_permission_changes_user(self):
        permission = Permission.objects.get(codename='change_user', content_type__app_label='auth')
        self.operator.user_permissions.add(permission)
        self.client.force_login(self.operator)

        response = self.client.post(reverse('toggle_usuario', args=[self.target.id]))

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.target.is_active)


class RolePermissionActionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.operator = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='operatorpass123'
        )
        self.group = Group.objects.create(name='Temporal')

    def test_eliminar_rol_get_does_not_delete_role(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('eliminar_rol', args=[self.group.id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Group.objects.filter(id=self.group.id).exists())

    def test_eliminar_rol_without_permission_does_not_delete_role(self):
        self.client.force_login(self.operator)

        response = self.client.post(reverse('eliminar_rol', args=[self.group.id]))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/accounts/login/', response['Location'])
        self.assertTrue(Group.objects.filter(id=self.group.id).exists())

# Create your tests here.
