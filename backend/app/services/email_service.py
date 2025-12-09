"""Email service for sending and receiving emails via Gmail SMTP."""
import smtplib
import imaplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models.discovered_supplier import DiscoveredSupplier
from app.models.email_thread import EmailThread
from app.models.email_message import EmailMessage
from app.models.medicine import Medicine

logger = logging.getLogger(__name__)


class EmailService:
    """Gmail SMTP service with demo mode for hackathon."""
    
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        
        # Email credentials from .env
        self.email_address = settings.EMAIL_ADDRESS
        self.email_password = settings.EMAIL_APP_PASSWORD
        self.demo_recipient = settings.EMAIL_DEMO_RECIPIENT
        
    def send_quote_request(
        self,
        db: Session,
        supplier: DiscoveredSupplier,
        medicine: Medicine,
        quantity: int
    ) -> EmailThread:
        """Send quote request email to supplier (demo: actually to kanhacet@gmail.com)."""
        
        # Generate professional email body
        email_body = self._generate_quote_request_email(
            supplier_name=supplier.name,
            medicine_name=medicine.name,
            medicine_dosage=medicine.dosage,
            quantity=quantity
        )
        
        # Determine recipients (DEMO MAGIC HERE)
        display_to = supplier.display_email  # Show this in UI
        actual_to = supplier.actual_email if self.demo_mode else supplier.display_email
        
        # Create subject with demo identifier
        if self.demo_mode:
            subject = f"[DEMO: {supplier.demo_identifier}] Bulk Procurement Inquiry - {medicine.name} {quantity} units"
        else:
            subject = f"Bulk Procurement Inquiry - {medicine.name} {quantity} units"
        
        # Send email via Gmail SMTP
        try:
            message_id = self._send_via_smtp(
                to=actual_to,
                subject=subject,
                body=email_body
            )
            
            logger.info(f"✉️ Email sent to {display_to} (actually: {actual_to})")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
        
        # Create thread in database
        thread = EmailThread(
            supplier_id=supplier.id,
            procurement_task_id=supplier.procurement_task_id,
            display_recipient=display_to,
            actual_recipient=actual_to,
            subject=subject,
            thread_identifier=message_id,
            status="AWAITING_REPLY"
        )
        db.add(thread)
        
        # Create outgoing message record
        msg_record = EmailMessage(
            thread_id=None,  # Will update after commit
            sender=self.email_address,
            recipient=actual_to,
            display_sender=self.email_address,
            display_recipient=display_to,
            subject=subject,
            body=email_body,
            is_from_agent=True,
            sent_at=datetime.utcnow()
        )
        
        db.commit()
        db.refresh(thread)
        
        # Update message with thread_id
        msg_record.thread_id = thread.id
        db.add(msg_record)
        
        # Update supplier stats
        supplier.emails_sent += 1
        supplier.last_email_sent_at = datetime.utcnow()
        db.commit()
        
        return thread
    
    def _send_via_smtp(self, to: str, subject: str, body: str) -> str:
        """Send email via Gmail SMTP and return message ID."""
        
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
        
        # Generate a pseudo message-ID for tracking
        message_id = f"<{datetime.utcnow().timestamp()}@pharmacy-ai>"
        return message_id
    
    def check_for_replies(self, db: Session) -> List[EmailMessage]:
        """Check Gmail inbox for replies from demo email (kanhacet@gmail.com)."""
        
        if not self.demo_mode:
            return []  # In production, check actual supplier emails
        
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')
            
            # Search for ALL emails from demo recipient (not just UNSEEN)
            # User may have read the email when replying
            logger.info(f"Searching for emails FROM {self.demo_recipient}...")
            status, messages = mail.search(None, f'(FROM "{self.demo_recipient}")')
            
            if status != 'OK':
                logger.warning(f"Search failed: {status}")
                return []
            
            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} total emails from {self.demo_recipient}")
            processed = []
            
            # Process only recent emails (last 20 to avoid reprocessing old ones)
            for email_id in email_ids[-20:]:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                subject = email_message['subject']
                from_addr = email_message['from']
                
                # Extract body
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                # Extract demo identifier from subject
                match = re.search(r'\[DEMO: (.*?)\]', subject)
                
                if not match:
                    logger.warning(f"Email from {from_addr} missing [DEMO: X] identifier")
                    continue
                
                demo_id = match.group(1)
                
                # Find supplier by demo_identifier
                supplier = db.query(DiscoveredSupplier).filter_by(
                    demo_identifier=demo_id
                ).first()
                
                if not supplier:
                    logger.warning(f"No supplier found for demo_id: {demo_id}")
                    continue
                
                # Find thread
                thread = db.query(EmailThread).filter_by(
                    supplier_id=supplier.id,
                    status="AWAITING_REPLY"
                ).first()
                
                if not thread:
                    logger.warning(f"No awaiting thread for supplier: {supplier.name}")
                    continue
                
                # Parse email for pricing info
                from app.services.email_parser import EmailParser
                parser = EmailParser()
                parsed = parser.parse_supplier_email(body)
                
                # Save message (with display addresses for UI)
                message = EmailMessage(
                    thread_id=thread.id,
                    sender=self.demo_recipient,
                    recipient=self.email_address,
                    display_sender=supplier.display_email,  # UI shows this!
                    display_recipient=self.email_address,
                    subject=subject,
                    body=body,
                    is_from_agent=False,
                    parsed_data=parsed,
                    quoted_price=parsed.get('price'),
                    delivery_days=parsed.get('delivery_days'),
                    received_at=datetime.utcnow()
                )
                db.add(message)
                
                # Update thread
                thread.status = "REPLIED"
                thread.last_activity = datetime.utcnow()
                
                # Update supplier stats
                supplier.emails_received += 1
                supplier.last_response_time = datetime.utcnow()
                supplier.is_responsive = True
                
                db.commit()
                
                logger.info(f"✅ Reply received from {supplier.display_email}: ${parsed.get('price')}/unit")
                
                processed.append(message)
                
                # Mark as read
                mail.store(email_id, '+FLAGS', '\\Seen')
            
            mail.close()
            mail.logout()
            
            return processed
            
        except Exception as e:
            logger.error(f"Error checking inbox: {e}")
            return []
    
    def _generate_quote_request_email(
        self,
        supplier_name: str,
        medicine_name: str,
        medicine_dosage: str,
        quantity: int
    ) -> str:
        """Generate professional quote request email."""
        
        return f"""Dear {supplier_name} Sales Team,

We are reaching out regarding a bulk procurement requirement for our pharmacy supply chain.

PRODUCT REQUEST:
- Medicine: {medicine_name}
- Dosage: {medicine_dosage}
- Quantity: {quantity} units
- Urgency: High Priority

We kindly request your best quotation including:
1. Unit price (please specify currency)
2. Delivery timeframe
3. Minimum order quantity (if applicable)
4. Payment terms
5. Product certifications

Please respond at your earliest convenience with your competitive pricing.

Best regards,
Procurement Department
Pharmacy Supply Chain AI
Email: {self.email_address}

---
This is an automated inquiry. Please reply with your quotation details.
"""
