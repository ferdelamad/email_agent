#!/usr/bin/env python3
"""
Simple email test script to verify SMTP configuration
without using the AI agent.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not available, using environment variables only")

def test_email_config():
    """Test email configuration and send a test email."""
    
    # Get configuration
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    sender_name = os.environ.get("SENDER_NAME", "Email Agent Test")
    
    print(f"📧 SMTP Server: {smtp_server}:{smtp_port}")
    print(f"📤 Sender: {sender_name} <{sender_email}>")
    
    # Check required configuration
    if not sender_email:
        print("❌ SENDER_EMAIL not set in environment variables")
        return False
    
    if not sender_password:
        print("❌ SENDER_PASSWORD not set in environment variables")
        return False
    
    # Get recipient details
    recipient_email = input("Enter recipient email: ").strip()
    if not recipient_email:
        print("❌ No recipient email provided")
        return False
    
    # Create test message
    subject = "Test Email from Email Agent"
    body = f"""Hello!

This is a test email from the Email Agent to verify SMTP configuration.

If you receive this email, the email sending functionality is working correctly.

Best regards,
{sender_name}
"""
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"🔄 Connecting to {smtp_server}:{smtp_port}...")
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        
        print("🔐 Starting TLS encryption...")
        print("🔑 Authenticating...")
        
        server.login(sender_email, sender_password)
        
        print("📨 Sending email...")
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 For Gmail:")
        print("   1. Enable 2-factor authentication")
        print("   2. Generate an App Password")
        print("   3. Use the App Password as SENDER_PASSWORD")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_config_template():
    """Show the configuration template."""
    print("\n📋 Configuration Template (.env file):")
    print("=" * 50)
    print("""# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# SMTP Email Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password-here
SENDER_NAME=Your Name

# SMTP Server Settings (Gmail defaults)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587""")
    print("=" * 50)

def main():
    print("🧪 Email Agent - SMTP Test")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Test email sending")
        print("2. Show configuration template")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🧪 Testing email configuration...")
            success = test_email_config()
            if success:
                print("\n🎉 Email test completed successfully!")
                print("Your SMTP configuration is working correctly.")
            else:
                print("\n❌ Email test failed.")
                print("Please check your configuration and try again.")
                
        elif choice == "2":
            show_config_template()
            
        elif choice == "3":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
