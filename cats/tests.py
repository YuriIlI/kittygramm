from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from cats.models import Cat, AdoptionApplication, StatusChangeLog

class AdoptionApplicationTests(APITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.cat = Cat.objects.create(name='Барсик', color='Gray', birth_year=2020, owner=self.admin)
        self.client.force_authenticate(user=self.user)

    def test_create_application_success(self):
        url = reverse('application-list')
        data = {'cat': self.cat.id, 'comment': 'Хочу усыновить Барсика'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AdoptionApplication.objects.count(), 1)
        self.assertEqual(AdoptionApplication.objects.first().status, 'pending')

    def test_create_application_duplicate(self):
        AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='first')
        url = reverse('application-list')
        data = {'cat': self.cat.id, 'comment': 'second'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cat', response.data)

    def test_create_application_cat_already_adopted(self):
        # Создаём завершённую заявку на кота
        AdoptionApplication.objects.create(user=self.admin, cat=self.cat, status='completed')
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {'cat': self.cat.id, 'comment': 'попытка'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cat', response.data)

    def test_comment_min_length(self):
        url = reverse('application-list')
        data = {'cat': self.cat.id, 'comment': 'коротко'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('comment', response.data)

    def test_user_can_view_own_applications(self):
        app = AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='моя')
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], app.id)

    def test_admin_can_view_all_applications(self):
        AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='user1')
        AdoptionApplication.objects.create(user=self.admin, cat=self.cat, comment='admin')
        self.client.force_authenticate(user=self.admin)
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_change_status_by_admin(self):
        app = AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='test')
        self.client.force_authenticate(user=self.admin)
        url = reverse('application-change-status', kwargs={'pk': app.pk})
        data = {'status': 'approved', 'note': 'одобрено'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, 'approved')
        self.assertEqual(StatusChangeLog.objects.count(), 1)
        log = StatusChangeLog.objects.first()
        self.assertEqual(log.old_status, 'pending')
        self.assertEqual(log.new_status, 'approved')
        self.assertEqual(log.changed_by, self.admin)

    def test_change_status_by_regular_user_forbidden(self):
        app = AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='test')
        url = reverse('application-change-status', kwargs={'pk': app.pk})
        data = {'status': 'approved'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_status_of_completed_application(self):
        app = AdoptionApplication.objects.create(user=self.user, cat=self.cat, status='completed', comment='test')
        self.client.force_authenticate(user=self.admin)
        url = reverse('application-change-status', kwargs={'pk': app.pk})
        data = {'status': 'rejected'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_access_owner(self):
        app = AdoptionApplication.objects.create(user=self.user, cat=self.cat, comment='test')
        StatusChangeLog.objects.create(application=app, changed_by=self.admin, old_status='pending', new_status='approved')
        url = reverse('application-history', kwargs={'pk': app.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_history_access_other_user_forbidden(self):
        other_user = User.objects.create_user(username='other', password='other')
        app = AdoptionApplication.objects.create(user=other_user, cat=self.cat, comment='test')
        url = reverse('application-history', kwargs={'pk': app.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # или 403 - зависит от get_queryset