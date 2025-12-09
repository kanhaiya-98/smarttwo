"""Test email sending directly."""
import sys
sys.path.append('.')

from app.config import settings
import smtplib
from email.mime.text import MIMEText
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email():
    """Test Gmail SMTP connection and sending."""
    
    logger.info("=" * 60)
    logger.info("Testing Email Configuration")
    logger.info("=" * 60)
    
    logger.info(f"From: {settings.EMAIL_ADDRESS}")
    logger.info(f"App Password: {'*' * 16 if settings.EMAIL_APP_PASSWORD else 'MISSING'}")
    logger.info(f"To: {settings.EMAIL_DEMO_RECIPIENT}")
    
    if not settings.EMAIL_ADDRESS or not settings.EMAIL_APP_PASSWORD:
        logger.error("❌ Email credentials not configured!")
        return
    
    try:
        # Create test message
        msg = MIMEText("This is a test email from Pharmacy Supply Chain AI.\n\nIf you receive this, email sending is working!")
        msg['Subject'] = "[TEST] Pharmacy AI Email Test"
        msg['From'] = settings.EMAIL_ADDRESS
        msg['To'] = settings.EMAIL_DEMO_RECIPIENT
        
        logger.info("\n🔌 Connecting to Gmail SMTP...")
        
        # Connect and send
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.set_debuglevel(1)  # Show SMTP conversation
            logger.info("✓ Connected")
            
            server.starttls()
            logger.info("✓ TLS started")
            
            server.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
            logger.info("✓ Logged in")
            
            server.send_message(msg)
            logger.info("✓ Email sent!")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ SUCCESS! Check kanhacet@gmail.com inbox")
        logger.info("=" * 60)
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"\n❌ Authentication failed: {e}")
        logger.error("Possible issues:")
        logger.error("  1. Incorrect email/password")
        logger.error("  2. 2-Factor Authentication not enabled")
        logger.error("  3. App Password not generated/expired")
        logger.error("  4. 'Less secure app access' disabled")
        
    except Exception as e:
        logger.error(f"\n❌ Email sending failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()
