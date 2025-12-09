"""Debug inbox check - see what emails are actually in Gmail."""
import sys
sys.path.append('.')

from app.config import settings
import imaplib
import email
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_inbox():
    """Check Gmail inbox and show all unread emails."""
    
    try:
        logger.info("🔌 Connecting to Gmail IMAP...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
        mail.select('inbox')
        
        # Get ALL unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK':
            logger.error("Failed to search inbox")
            return
        
        email_ids = messages[0].split()
        logger.info(f"\n📧 Found {len(email_ids)} UNREAD emails in inbox")
        
        for i, email_id in enumerate(email_ids[-5:], 1):  # Show last 5
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject = email_message['subject']
            from_addr = email_message['from']
            
            logger.info(f"\n--- Email {i} ---")
            logger.info(f"From: {from_addr}")
            logger.info(f"Subject: {subject}")
            
            # Check for [DEMO: X]
            import re
            match = re.search(r'\[DEMO: (.*?)\]', subject)
            if match:
                logger.info(f"✓ Has DEMO tag: {match.group(1)}")
            else:
                logger.info("✗ NO DEMO tag found")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_inbox()
