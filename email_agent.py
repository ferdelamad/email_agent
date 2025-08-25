import json
import os
import smtplib
import anthropic
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Callable, Tuple

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable[[Dict[str, Any]], Tuple[str, Optional[str]]]
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.function = function

class Agent:
    def __init__(
        self,
        client: anthropic.Anthropic,
        get_user_message: Callable[[], Tuple[str, bool]],
        tools: List[ToolDefinition]
    ):
        self.client = client
        self.get_user_message = get_user_message
        self.tools = tools
    
    def run_inference(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })
        
        message = self.client.messages.create(
            model="claude-3-5-haiku-20241022", #"claude-3-5-sonnet-latest",
            max_tokens=1024,
            messages=conversation,
            tools=anthropic_tools if anthropic_tools else []
        )
        return message
    
    def execute_tool(self, tool_id: str, name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        tool_def = None
        for tool in self.tools:
            if tool.name == name:
                tool_def = tool
                break
        
        if tool_def is None:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": "tool not found",
                "is_error": True
            }
        
        print(f"\u001b[92mtool\u001b[0m: {name}({json.dumps(input_data)})")
        result, error = tool_def.function(input_data)
        
        if error:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": error,
                "is_error": True
            }
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": result,
            "is_error": False
        }
    
    def run(self):
        conversation = []
        
        # Add system message with instructions
        system_message = {
            "role": "user",
            "content": [{
                "type": "text", 
                "text": """You are an email agent assistant. Follow these rules:

1. NEVER use placeholder emails (like frank@example.com). If an email address is missing, ask the user for it.
2. ALWAYS use the review_email tool to show the email preview and get user confirmation BEFORE sending any email.
3. The workflow should be: generate_email → review_email → (if approved) send_email
4. If the user doesn't provide required information (recipient email, name, or message), ask for it explicitly.

Available tools:
- generate_email: Create professional emails from rough input
- review_email: Show email preview and get user confirmation 
- send_email: Actually send the email (only after review approval)"""
            }]
        }
        conversation.append(system_message)
        
        print("\n\u001b[1mEmail Agent - Chat with Claude\u001b[0m")
        print("I can help you generate and send professional emails!")
        print("Type your messages and press Enter to chat")
        print("Press Ctrl+C to exit\n")
        
        read_user_input = True
        while True:
            if read_user_input:
                print("\u001b[94mYou\u001b[0m: ", end="")
                user_input, ok = self.get_user_message()
                if not ok:
                    break
                
                user_message = {
                    "role": "user",
                    "content": [{"type": "text", "text": user_input}]
                }
                conversation.append(user_message)
            
            message = self.run_inference(conversation)
            
            assistant_message = {
                "role": "assistant",
                "content": []
            }
            
            tool_results = []
            for content in message.content:
                if content.type == "text":
                    print(f"\u001b[93mClaude\u001b[0m: {content.text}")
                    assistant_message["content"].append({
                        "type": "text",
                        "text": content.text
                    })
                elif content.type == "tool_use":
                    result = self.execute_tool(content.id, content.name, content.input)
                    tool_results.append(result)
                    assistant_message["content"].append({
                        "type": "tool_use",
                        "id": content.id,
                        "name": content.name,
                        "input": content.input
                    })
            
            conversation.append(assistant_message)
            
            if not tool_results:
                read_user_input = True
                continue
            
            read_user_input = False
            conversation.append({
                "role": "user",
                "content": tool_results
            })

# Email Tool Definitions
def generate_email(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Generate a professional email from rough input."""
    try:
        recipient_email = input_data.get("recipient_email", "")
        recipient_name = input_data.get("recipient_name", "")
        rough_message = input_data.get("rough_message", "")
        subject = input_data.get("subject", "")
        
        # Check if required fields are missing - DO NOT use placeholder emails
        missing_fields = []
        if not recipient_email:
            missing_fields.append("recipient_email")
        if not recipient_name:
            missing_fields.append("recipient_name")
        if not rough_message:
            missing_fields.append("rough_message")
        
        if missing_fields:
            return "", f"I need more information to generate the email. Please provide: {', '.join(missing_fields)}. Do not use placeholder emails - I need the actual recipient's email address."
        
        # Create a professional email structure
        email_content = {
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "subject": subject if subject else "Professional Communication",
            "body": f"""Dear {recipient_name},

{rough_message}

Best regards,
[Your Name]"""
        }
        
        return json.dumps(email_content, indent=2), None
        
    except Exception as e:
        return "", str(e)

generate_email_definition = ToolDefinition(
    name="generate_email",
    description="Generate a professional email from rough input. Requires recipient email, name, and rough message content. Always ask the user for missing information instead of using placeholders.",
    input_schema={
        "type": "object",
        "properties": {
            "recipient_email": {
                "type": "string",
                "description": "Email address of the recipient - REQUIRED, do not use placeholders"
            },
            "recipient_name": {
                "type": "string",
                "description": "Name of the recipient - REQUIRED"
            },
            "rough_message": {
                "type": "string",
                "description": "The rough message content to be made professional - REQUIRED"
            },
            "subject": {
                "type": "string",
                "description": "Optional email subject line"
            }
        },
        "required": ["recipient_email", "recipient_name", "rough_message"]
    },
    function=generate_email
)


def review_email(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Display email for review and get user confirmation before sending."""
    try:
        recipient_email = input_data.get("recipient_email", "")
        subject = input_data.get("subject", "")
        body = input_data.get("body", "")
        
        if not recipient_email or not subject or not body:
            return "", "Missing required fields: recipient_email, subject, and body are all required for review"
        
        # Display email in a nice format
        print("\n" + "="*60)
        print("📧 EMAIL PREVIEW")
        print("="*60)
        print(f"📤 To: {recipient_email}")
        print(f"📋 Subject: {subject}")
        print("-"*60)
        print("📝 Body:")
        print(body)
        print("="*60)
        
        # Ask for confirmation with Claude styling
        while True:
            print(f"\n\u001b[93mClaude\u001b[0m: Do you want to send this email? (y/n): ", end="")
            response = input().strip().lower()
            if response in ['y', 'yes']:
                return "Email approved for sending", None
            elif response in ['n', 'no']:
                return "", "Email sending cancelled by user"
            else:
                print(f"\u001b[93mClaude\u001b[0m: Please enter 'y' for yes or 'n' for no")
        
    except Exception as e:
        return "", str(e)


review_email_definition = ToolDefinition(
    name="review_email",
    description="Display the email in a nice format and ask for user confirmation before sending. Use this BEFORE sending any email.",
    input_schema={
        "type": "object",
        "properties": {
            "recipient_email": {
                "type": "string",
                "description": "Email address of the recipient"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "body": {
                "type": "string",
                "description": "Email body content"
            }
        },
        "required": ["recipient_email", "subject", "body"]
    },
    function=review_email
)

def send_email(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Send an email via SMTP."""
    try:
        recipient_email = input_data.get("recipient_email", "")
        subject = input_data.get("subject", "")
        body = input_data.get("body", "")
        
        if not recipient_email or not subject or not body:
            return "", "Missing required fields: recipient_email, subject, and body are all required"
        
        # Get SMTP configuration from environment variables
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        sender_email = os.environ.get("SENDER_EMAIL")
        sender_password = os.environ.get("SENDER_PASSWORD")
        sender_name = os.environ.get("SENDER_NAME", "Email Agent")
        
        if not sender_email or not sender_password:
            return "", "SMTP configuration missing. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return f"Email sent successfully to {recipient_email}", None
        
    except Exception as e:
        return "", f"Failed to send email: {str(e)}"

send_email_definition = ToolDefinition(
    name="send_email",
    description="Send an email via SMTP. Requires recipient_email, subject, and body.",
    input_schema={
        "type": "object",
        "properties": {
            "recipient_email": {
                "type": "string",
                "description": "Email address of the recipient"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "body": {
                "type": "string",
                "description": "Email body content"
            }
        },
        "required": ["recipient_email", "subject", "body"]
    },
    function=send_email
)

def main():
    # Try to load from .env file if available
    if DOTENV_AVAILABLE:
        load_dotenv()
    
    # Get API key from environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY environment variable not set")
        api_key = input("Please enter your Anthropic API key: ")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    def get_user_message() -> Tuple[str, bool]:
        try:
            return input(), True
        except (EOFError, KeyboardInterrupt):
            return "", False
    
    # Initialize tools
    tools = [generate_email_definition, review_email_definition, send_email_definition]
    agent = Agent(client, get_user_message, tools)
    
    try:
        agent.run()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
