import imaplib
import email
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any, List
import re
from ..models.content_models import ContentRequest, ContentType, Priority
from config.logging_config import get_logger


class EmailHandler:
    def __init__(self, email_config: Dict[str, str]):
        self.logger = get_logger(__name__)
        self.imap_server = email_config.get("imap_server")
        self.smtp_server = email_config.get("smtp_server")
        self.email_address = email_config.get("email_address")
        self.password = email_config.get("password")
        self.smtp_port = email_config.get("smtp_port", 587)
        self.logger.info(f"Email Handler initialized for {self.email_address}")

    def check_for_requests(self) -> List[ContentRequest]:
        """Check email for content requests"""
        self.logger.info("Checking for email content requests...")
        requests = []

        try:
            # Connect to IMAP server
            self.logger.debug(f"Connecting to IMAP server: {self.imap_server}")
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            mail.select("inbox")

            # Search for unread emails
            status, message_ids = mail.search(None, "UNSEEN")
            email_count = len(message_ids[0].split()) if message_ids[0] else 0

            self.logger.info(f"Found {email_count} unread emails")

            for msg_id in message_ids[0].split():
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                email_message = email.message_from_bytes(msg_data[0][1])

                # Parse email into content request
                request = self._parse_email_to_request(email_message)
                if request:
                    requests.append(request)
                    self.logger.info(
                        f"Parsed content request from email: {request.topic}"
                    )

            mail.close()
            mail.logout()

            self.logger.info(
                f"✅ Email check completed: {len(requests)} content requests found"
            )

        except Exception as e:
            self.logger.error(f"❌ Error checking emails: {e}", exc_info=True)

        return requests

    def _parse_email_to_request(self, email_message) -> ContentRequest:
        """Parse email into ContentRequest"""
        self.logger.debug("Parsing email into content request")

        subject = email_message["subject"] or ""
        body = ""

        # Extract email body
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        self.logger.debug(f"Email subject: {subject[:50]}..., body length: {len(body)}")

        # Parse content request from subject and body
        content_type = self._extract_content_type(subject + " " + body)
        priority = self._extract_priority(subject + " " + body)

        # Extract other fields using simple heuristics
        topic = self._extract_topic(subject, body)
        target_audience = self._extract_audience(body)
        key_points = self._extract_key_points(body)

        request = ContentRequest(
            topic=topic,
            content_type=content_type,
            priority=priority,
            target_audience=target_audience,
            key_points=key_points,
            additional_context=body[:500],  # First 500 chars as context
        )

        self.logger.debug(
            f"Parsed request: {content_type.value}, {priority.value}, {len(key_points)} key points"
        )
        return request

    def _extract_content_type(self, text: str) -> ContentType:
        """Extract content type from email text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["blog", "article", "post"]):
            return ContentType.BLOG_POST
        elif any(
            word in text_lower for word in ["social", "twitter", "facebook", "linkedin"]
        ):
            return ContentType.SOCIAL_MEDIA
        elif any(word in text_lower for word in ["newsletter", "email"]):
            return ContentType.EMAIL_NEWSLETTER
        elif any(word in text_lower for word in ["product", "description"]):
            return ContentType.PRODUCT_DESCRIPTION
        elif any(word in text_lower for word in ["landing", "page"]):
            return ContentType.LANDING_PAGE

        return ContentType.BLOG_POST  # Default

    def _extract_priority(self, text: str) -> Priority:
        """Extract priority from email text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["urgent", "asap", "immediate"]):
            return Priority.URGENT
        elif any(word in text_lower for word in ["high", "important"]):
            return Priority.HIGH
        elif any(word in text_lower for word in ["low", "whenever"]):
            return Priority.LOW

        return Priority.MEDIUM  # Default

    def _extract_topic(self, subject: str, body: str) -> str:
        """Extract main topic from email"""
        # Use subject as primary topic, fallback to first sentence of body
        if subject and not subject.lower().startswith("re:"):
            return subject.strip()

        # Extract first meaningful sentence from body
        sentences = re.split(r"[.!?]+", body)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Meaningful sentence
                return sentence[:100]  # Limit length

        return "Content request"

    def _extract_audience(self, body: str) -> str:
        """Extract target audience from body"""
        # Look for audience indicators
        audience_patterns = [
            r"audience[:\s]+([^.]+)",
            r"target[:\s]+([^.]+)",
            r"for[:\s]+([^.]+)",
        ]

        for pattern in audience_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]

        return None

    def _extract_key_points(self, body: str) -> List[str]:
        """Extract key points from body"""
        key_points = []

        # Look for bullet points or numbered lists
        bullet_patterns = [
            r"[•\-\*]\s+([^•\-\*\n]+)",
            r"\d+\.\s+([^\d\n]+)",
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, body)
            key_points.extend([match.strip() for match in matches])

        return key_points[:5]  # Limit to 5 key points

    def send_response(
        self, to_email: str, subject: str, content: str, draft: Dict[str, Any] = None
    ) -> bool:
        """Send email response with content"""
        self.logger.info(f"Sending email response to: {to_email}")

        try:
            msg = MimeMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = f"Re: {subject}"

            # Create email body
            if draft:
                email_body = f"""
                Content ready for review:
                
                Title: {draft.get('title', 'N/A')}
                Word Count: {draft.get('word_count', 'N/A')}
                Quality Score: {draft.get('quality_score', 'N/A')}
                
                Content:
                {content}
                
                Please review and provide feedback.
                """
                self.logger.debug(
                    f"Email body includes draft info: {draft.get('title')}"
                )
            else:
                email_body = content
                self.logger.debug("Email body contains content only")

            msg.attach(MimeText(email_body, "plain"))

            # Send email
            self.logger.debug(
                f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}"
            )
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.password)
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()

            self.logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            self.logger.error(
                f"❌ Error sending email to {to_email}: {e}", exc_info=True
            )
            return False
