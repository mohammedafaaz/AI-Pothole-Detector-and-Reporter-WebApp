#!/usr/bin/env python3
"""
Test script to verify email configuration
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_config():
    """Test email configuration and send a test email"""
    
    # Get email configuration
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    admin_email = os.getenv('ADMIN_EMAIL')
    
    print("Email Configuration Test")
    print("=" * 40)
    print(f"EMAIL_USER: {email_user}")
    print(f"EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'Not set'}")
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    print(f"ADMIN_EMAIL: {admin_email}")
    print()
    
    # Check if all required fields are present
    if not email_user:
        print("[ERROR] EMAIL_USER is not set")
        return False
    
    if not email_password:
        print("[ERROR] EMAIL_PASSWORD is not set")
        return False
    
    if not admin_email:
        print("[ERROR] ADMIN_EMAIL is not set")
        return False
    
    print("[OK] All email configuration fields are present")
    print()
    
    # Test SMTP connection
    try:
        print("Testing SMTP connection...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print(f"[OK] Connected to {smtp_server}:{smtp_port}")
            
            server.starttls(context=context)
            print("[OK] TLS connection established")
            
            server.login(email_user, email_password)
            print("[OK] Authentication successful")
            
            # Send test email
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = admin_email
            msg['Subject'] = "Test Email - FixMyPothole.AI Configuration"
            
            body = """
            This is a test email to verify that your email configuration is working correctly.
            
            If you receive this email, your email service is properly configured for the FixMyPothole.AI application.
            
            Configuration Details:
            - SMTP Server: {}
            - SMTP Port: {}
            - From Email: {}
            - To Email: {}
            
            Best regards,
            FixMyPothole.AI System
            """.format(smtp_server, smtp_port, email_user, admin_email)
            
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            print(f"[OK] Test email sent successfully to {admin_email}")
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] Authentication failed: {e}")
        print("   Check your email and app password")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_email_config()
    
    if success:
        print("\n[SUCCESS] Email configuration test completed successfully!")
        print("You should receive a test email shortly.")
    else:
        print("\n[FAILED] Email configuration test failed!")
        print("Please check your .env file and email settings.")