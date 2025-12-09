"""Find emails FROM kanhacet@gmail.com (user's replies)."""
import sys
sys.path.append('.')

from app.config import settings
import imaplib
import email
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_replies():
    """Find emails FROM kanhacet@gmail.com."""
    
    try:
        logger.info("🔌 Connecting to Gmail IMAP...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
        mail.select('inbox')
        
        # Search for emails FROM kanhacet@gmail.com
        search_query = f'(FROM "{settings.EMAIL_DEMO_RECIPIENT}")'
        status, messages = mail.search(None, search_query)
        
        if status != 'OK':
            logger.error("Failed to search inbox")
            return
        
        email_ids = messages[0].split()
        logger.info(f"\n📧 Found {len(email_ids)} emails FROM {settings.EMAIL_DEMO_RECIPIENT}")
        
        for i, email_id in enumerate(email_ids[-10:], 1):  # Show last 10
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject = email_message['subject'] or ""
            date = email_message['date'] or ""
            
            logger.info(f"\n--- Reply {i} ---")
            logger.info(f"Date: {date}")
            logger.info(f"Subject: {subject}")
            
            # Check for [DEMO: X]
            match = re.search(r'\[DEMO: (.*?)\]', subject)
            if match:
                logger.info(f"✓ Has DEMO tag: '{match.group(1)}'")
            else:
                logger.info("✗ NO DEMO tag - This won't be detected!")
                logger.info("   Expected format: [DEMO: SupplierName] ...")
            
            # Show body preview
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()[:200]
                        logger.info(f"Body preview: {body}...")
                        break
            else:
                body = email_message.get_payload(decode=True).decode()[:200]
                logger.info(f"Body preview: {body}...")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_replies()
