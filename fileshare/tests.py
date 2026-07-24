from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets

from fileshare.models import SharedFile
from fileshare.interfaces import DBInterface, D1Client
from links.models import ShortLink
from links.interfaces import ShortLinkDBInterface
from django_ratelimit.exceptions import Ratelimited


class TempestFullStackTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Reset the test database for each run
        D1Client._test_conn = None

    def test_landing_page(self):
        """Verify the landing page renders successfully."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tempest")

    def test_upload_page_get(self):
        """Verify the upload page renders GET request successfully."""
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)

    def test_d1_database_offline_behavior(self):
        """Test D1Client local sqlite fallback for inserts and queries."""
        file_id = str(uuid.uuid4())
        shared_file = SharedFile(
            id=file_id,
            token="testtoken123",
            file_name="test_file.txt",
            original_name="test.txt",
            uploaded_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1),
            max_downloads=5,
            download_count=0
        )
        DBInterface.create_shared_file(shared_file)

        retrieved = DBInterface.get_file_by_uuid(file_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, file_id)
        self.assertEqual(retrieved.original_name, "test.txt")
        self.assertEqual(retrieved.max_downloads, 5)

    def test_short_link_redirection_and_increment(self):
        """Test that short link resolves, redirects, and increments the download counts."""
        file_id = str(uuid.uuid4())
        file_token = "tok12345"
        shared_file = SharedFile(
            id=file_id,
            token=file_token,
            file_name="realfile.png",
            original_name="real.png",
            uploaded_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=2),
            max_downloads=10,
            download_count=0
        )
        DBInterface.create_shared_file(shared_file)

        # Create ShortLink
        link_id = str(uuid.uuid4())
        short_link = ShortLink(
            id=link_id,
            code="abcxyz12",
            shared_file_id=file_id,
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=2),
            max_downloads=10,
            download_count=0,
            is_active=True
        )
        ShortLinkDBInterface.create_short_link(short_link)

        # Execute redirect request
        response = self.client.get(reverse('short_redirect', kwargs={'code': 'abcxyz12'}))
        
        # Verify it redirects to the download page
        self.assertEqual(response.status_code, 302)
        self.assertIn("/download/", response.url)

        # Verify usage was incremented
        updated_link = ShortLinkDBInterface.get_link_by_code("abcxyz12")
        self.assertEqual(updated_link.download_count, 1)

    def test_expired_file_redirects_to_expired_page(self):
        """Verify accessing an expired link renders the link_expired template."""
        file_id = str(uuid.uuid4())
        file_token = "tok999"
        # Already expired 1 hour ago
        shared_file = SharedFile(
            id=file_id,
            token=file_token,
            file_name="old.zip",
            original_name="old.zip",
            uploaded_at=timezone.now() - timedelta(hours=2),
            expires_at=timezone.now() - timedelta(hours=1),
            max_downloads=5,
            download_count=0
        )
        DBInterface.create_shared_file(shared_file)

        # Get download view
        from fileshare.views import get_obfuscated_token
        secure_token = get_obfuscated_token(file_token)
        
        response = self.client.get(reverse('download', kwargs={'token': secure_token, 'original_uuid': file_id}))
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'link_expired.html')

    def test_ratelimit_middleware_renders_429(self):
        """Verify RatelimitMiddleware catches Ratelimited exceptions and returns 429 status and page."""
        # We can trigger it by raising a Ratelimited exception during a view call or mocking it
        # Let's test by requesting a path and verifying that the middleware catches the exception.
        # To simulate a Ratelimited exception, we can call a view that is explicitly patched to raise it.
        from unittest.mock import patch
        from django.http import HttpResponse

        with patch('fileshare.views.landing_view', side_effect=Ratelimited):
            response = self.client.get(reverse('landing'))
            self.assertEqual(response.status_code, 429)
            self.assertTemplateUsed(response, '429.html')
