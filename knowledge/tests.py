from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from datetime import timedelta

from django.utils import timezone

from .models import BlogPost, Category, ContactMessage, Note, Profile, RateLimitBucket, SavedContent, Tag
from .validators import validate_attachment

User = get_user_model()


class WebsiteWorkflowTests(TestCase):
    def setUp(self):
        RateLimitBucket.objects.all().delete()
        self.category, _ = Category.objects.get_or_create(name="Python", defaults={"slug": "python"})
        self.tag = Tag.objects.create(name="Foundations", slug="foundations")
        self.reader = User.objects.create_user(username="reader", email="reader@example.test", password="A-strong-password-938!")
        self.note = Note.objects.create(
            title="A useful Python note",
            slug="useful-python-note",
            summary="A practical explanation.",
            body="## The idea\n\nA clear explanation with `code`.",
            category=self.category,
            author=self.reader,
            status="published",
            published_at=timezone.now(),
        )
        self.note.tags.add(self.tag)
        self.post = BlogPost.objects.create(
            title="Learning in public",
            slug="learning-in-public",
            summary="A journal entry.",
            body="## Notes from the work\n\nAn example.",
            author=self.reader,
            status="published",
            published_at=timezone.now(),
        )

    def test_home_and_public_content_routes_render_published_content(self):
        self.assertContains(self.client.get("/"), "Make the hard")
        self.assertContains(self.client.get("/notes/"), "A useful Python note")
        self.assertContains(self.client.get("/notes/useful-python-note/"), "The idea")
        self.assertContains(self.client.get("/blog/"), "Learning in public")
        self.assertContains(self.client.get("/blog/learning-in-public/"), "Notes from the work")

    def test_drafts_and_scheduled_content_are_not_public(self):
        draft = Note.objects.create(
            title="Private draft", slug="private-draft", summary="Not public", body="Draft body",
            category=self.category, author=self.reader, status="draft",
        )
        scheduled = BlogPost.objects.create(
            title="Future entry", slug="future-entry", summary="Not yet", body="Scheduled",
            author=self.reader, status="published", published_at=timezone.now() + timedelta(days=1),
        )
        self.assertEqual(self.client.get(f"/notes/{draft.slug}/").status_code, 404)
        self.assertEqual(self.client.get(f"/blog/{scheduled.slug}/").status_code, 404)
        self.assertNotContains(self.client.get("/notes/"), draft.title)

    def test_search_and_filters_return_matching_records(self):
        response = self.client.get("/search/", {"q": "Python"})
        self.assertContains(response, self.note.title)
        response = self.client.get("/notes/", {"category": "python", "tag": "foundations"})
        self.assertContains(response, self.note.title)
        self.assertNotContains(self.client.get("/search/", {"q": "nonexistent-term"}), self.note.title)

    def test_signup_creates_profile_and_stores_hashed_password(self):
        response = self.client.post("/signup/", {
            "username": "new-reader",
            "email": "New.Reader@example.test",
            "password1": "Another-strong-password-482!",
            "password2": "Another-strong-password-482!",
        })
        self.assertRedirects(response, "/profile/")
        user = User.objects.get(username="new-reader")
        self.assertEqual(user.email, "new.reader@example.test")
        self.assertTrue(user.check_password("Another-strong-password-482!"))
        self.assertNotEqual(user.password, "Another-strong-password-482!")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_login_logout_and_private_profile_access(self):
        anonymous = self.client.get("/profile/")
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn("/login/", anonymous["Location"])
        response = self.client.post("/login/", {"username": "reader", "password": "A-strong-password-938!"})
        self.assertRedirects(response, "/profile/")
        self.assertContains(self.client.get("/profile/"), "Profile & preferences")
        self.assertRedirects(self.client.post("/accounts/logout/"), "/")

    def test_profile_form_updates_member_details(self):
        self.client.force_login(self.reader)
        response = self.client.post("/profile/", {
            "first_name": "Casey", "last_name": "Reader", "bio": "Learning in public.", "website": "https://example.test",
        })
        self.assertRedirects(response, "/profile/")
        self.reader.refresh_from_db()
        self.reader.profile.refresh_from_db()
        self.assertEqual(self.reader.get_full_name(), "Casey Reader")
        self.assertEqual(self.reader.profile.bio, "Learning in public.")

    def test_upload_allowlist_rejects_unsafe_and_malformed_files(self):
        with self.assertRaises(ValidationError):
            validate_attachment(SimpleUploadedFile("payload.html", b"<script>no</script>"))
        with self.assertRaises(ValidationError):
            validate_attachment(SimpleUploadedFile("not-really.pdf", b"not a PDF"))
        validate_attachment(SimpleUploadedFile("guide.pdf", b"%PDF-1.7\nexample"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_one_time_link_and_changes_password(self):
        response = self.client.post("/accounts/password_reset/", {"email": self.reader.email})
        self.assertRedirects(response, "/accounts/password_reset/done/")
        self.assertEqual(len(mail.outbox), 1)
        link = next(part for part in mail.outbox[0].body.split() if "/accounts/reset/" in part)
        path = link.split("testserver", 1)[-1]
        self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.post(path, {
            "new_password1": "Brand-new-secure-password-932!",
            "new_password2": "Brand-new-secure-password-932!",
        })
        self.assertRedirects(response, "/accounts/reset/done/")
        self.reader.refresh_from_db()
        self.assertTrue(self.reader.check_password("Brand-new-secure-password-932!"))

    def test_saved_content_requires_login_and_persists(self):
        self.assertEqual(self.client.post(f"/save/note/{self.note.slug}/").status_code, 302)
        self.client.force_login(self.reader)
        response = self.client.post(f"/save/note/{self.note.slug}/", {"next": f"/notes/{self.note.slug}/", "intent": "save"})
        self.assertRedirects(response, f"/notes/{self.note.slug}/")
        self.assertTrue(SavedContent.objects.filter(user=self.reader, note=self.note).exists())
        self.assertContains(self.client.get("/saved/"), self.note.title)
        self.client.post(f"/save/note/{self.note.slug}/", {"intent": "remove"})
        self.assertFalse(SavedContent.objects.filter(user=self.reader, note=self.note).exists())

    def test_contact_form_persists_valid_message_and_rejects_invalid_input(self):
        invalid = self.client.post("/contact/", {"name": "", "email": "bad", "subject": "", "message": ""})
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        response = self.client.post("/contact/", {
            "name": "Casey Reader", "email": "casey@example.test", "subject": "A topic suggestion", "message": "Please add a guide.",
        })
        self.assertRedirects(response, "/contact/")
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_admin_dashboard_is_staff_only(self):
        self.assertEqual(self.client.get("/manage/").status_code, 302)
        staff = User.objects.create_user(username="editor", password="Editor-password-482!", is_staff=True)
        self.client.force_login(staff)
        self.assertContains(self.client.get("/manage/"), "Publishing overview")

    def test_markdown_output_is_sanitized(self):
        self.note.body = "Safe text\n\n<script>alert('no')</script>"
        self.note.save()
        response = self.client.get(f"/notes/{self.note.slug}/")
        self.assertContains(response, "Safe text")
        self.assertNotContains(response, "<script>")
