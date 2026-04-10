"""
Unit tests for server/mailserver/service.py
Tests: send_email, welcome_message
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os


class TestSendEmail:
    """Tests for send_email()"""

    def test_returns_message_schema(self, tmp_path):
        """Test that send_email returns a MessageSchema when template exists."""
        from mailserver.service import send_email
        
        # Create a temporary template file
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "test_template.html"
        template_file.write_text("<html>Hello {{ name }}</html>")
        
        with patch("mailserver.service.BASE_DIR", tmp_path):
            result = send_email(
                recepients=["test@test.com"],
                subject="Test Subject",
                html_message_path="test_template.html",
                data_variables={"name": "John"}
            )
            assert result is not None
            assert result.subject == "Test Subject"

    def test_handles_none_data_variables(self, tmp_path):
        """BUG-26 fix: send_email should not crash when data_variables is None."""
        from mailserver.service import send_email
        
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "plain.html"
        template_file.write_text("<html>No variables here</html>")
        
        with patch("mailserver.service.BASE_DIR", tmp_path):
            # This should NOT raise TypeError
            result = send_email(
                recepients=["test@test.com"],
                subject="No vars",
                html_message_path="plain.html",
                data_variables=None
            )
            assert result is not None

    def test_renders_template_variables(self, tmp_path):
        """Test that Jinja2 template variables are replaced."""
        from mailserver.service import send_email
        
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "link.html"
        template_file.write_text('<a href="{{ link }}">Click here</a>')
        
        with patch("mailserver.service.BASE_DIR", tmp_path):
            result = send_email(
                recepients=["user@test.com"],
                subject="Verify",
                html_message_path="link.html",
                data_variables={"link": "http://example.com/verify/abc"}
            )
            assert "http://example.com/verify/abc" in result.body

    def test_multiple_recipients(self, tmp_path):
        """Test sending to multiple recipients."""
        from mailserver.service import send_email
        
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "multi.html"
        template_file.write_text("<p>Hello</p>")
        
        with patch("mailserver.service.BASE_DIR", tmp_path):
            result = send_email(
                recepients=["a@test.com", "b@test.com", "c@test.com"],
                subject="Broadcast",
                html_message_path="multi.html",
                data_variables={}
            )
            assert len(result.recipients) == 3

    def test_raises_for_missing_template(self):
        """Test that missing template file raises an error."""
        from mailserver.service import send_email
        
        with pytest.raises(FileNotFoundError):
            send_email(
                recepients=["test@test.com"],
                subject="Test",
                html_message_path="nonexistent_template_xyz.html",
                data_variables={}
            )
