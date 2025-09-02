import json
import os
import smtplib
import anthropic
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

class Agent:
  def __init__(self, client, get_user_message, tools):
    self.client = client
    self.get_user_message = get_user_message
    self.tools = tools

  def run_inference(self, conversation):
    # Prepare tools for the API
    anthropic_tools = []
    for tool in self.tools:
      anthropic_tools.append({
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema
      })
    
    # Call the LLM with conversation history and available tools
    message = self.client.messages.create(
      model="claude-3-5-haiku-20241022",
      max_tokens=1024,
      messages=conversation,
      tools=anthropic_tools if anthropic_tools else []
    )

    return message

  def execute_tool(self, tool_id, name, input_data):
    # Find the tool definition
    tool_def = None
    for tool in self.tools:
      if tool.name == name:
        tool_def = tool
        break
    
    # Handle tool not found
    if tool_def is None:
      return {
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": "tool not found",
        "is_error": True
      }
    
    # Execute the tool and show what's happening
    print(f"\u001b[92mtool\u001b[0m: {name}({json.dumps(input_data)})")
    result, error = tool_def.function(input_data)
    
    # Return error if tool execution failed
    if error:
      return {
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": error,
        "is_error": True
      }
    
    # Return successful result
    return {
      "type": "tool_result",
      "tool_use_id": tool_id,
      "content": result,
      "is_error": False
    }

  def run(self):
    conversation = []
    
    # Define agent behavior through system message
    system_message = {
      "role": "user",
      "content": [{
        "type": "text", 
        "text": """You are an email agent assistant. Follow these rules:

          1. NEVER use placeholder emails. If an email address is missing, ask for it.
          2. ALWAYS use review_email before send_email to get user confirmation.
          3. Follow the workflow: generate_email → review_email → send_email
          4. If required information is missing, ask for it explicitly.
          5. After review_email approval, proceed directly to send_email without asking again.

          Available tools:
            - generate_email: Create professional emails from rough input
            - review_email: Show preview and get confirmation
            - send_email: Send the email via SMTP"""
      }]
    }
    conversation.append(system_message)
    
    # Display welcome message
    print("\n\u001b[1mEmail Agent - Chat with Claude\u001b[0m")
    print("I can help you generate and send professional emails!")
    print("Type your messages and press Enter to chat")
    print("Press Ctrl+C to exit\n")
    
    # Main conversation loop
    read_user_input = True
    while True:
      # Get user input when needed
      if read_user_input:
        print("\u001b[94mYou\u001b[0m: ", end="")
        user_input, ok = self.get_user_message()
        if not ok:
          break
        
        # Add user message to conversation
        user_message = {
          "role": "user",
          "content": [{"type": "text", "text": user_input}]
        }
        conversation.append(user_message)
      
      # Get LLM response
      message = self.run_inference(conversation)
      
      # Process assistant response
      assistant_message = {
        "role": "assistant",
        "content": []
      }
      
      tool_results = []
      for content in message.content:
        if content.type == "text":
          # Display text response
          print(f"\u001b[93mClaude\u001b[0m: {content.text}")
          assistant_message["content"].append({
            "type": "text",
            "text": content.text
          })
        elif content.type == "tool_use":
          # Execute tool and collect results
          result = self.execute_tool(content.id, content.name, content.input)
          tool_results.append(result)
          assistant_message["content"].append({
            "type": "tool_use",
            "id": content.id,
            "name": content.name,
            "input": content.input
          })
      
      # Add assistant response to conversation
      conversation.append(assistant_message)
      
      # Handle tool results
      if not tool_results:
        read_user_input = True
        continue
      
      # Add tool results to conversation for next iteration
      read_user_input = False
      conversation.append({
        "role": "user",
        "content": tool_results
      })
    
class ToolDefinition:
  def __init__(self, name, description, input_schema, function):
    self.name = name
    self.description = description
    self.input_schema = input_schema
    self.function = function

  @staticmethod
  def generate_email(input_data):
    """Generate a professional email from rough input."""
    try:
      # Extract input parameters
      recipient_email = input_data.get("recipient_email", "")
      recipient_name = input_data.get("recipient_name", "")
      rough_message = input_data.get("rough_message", "")
      subject = input_data.get("subject", "")
      
      # Validate required fields
      missing_fields = []
      if not recipient_email:
        missing_fields.append("recipient_email")
      if not recipient_name:
        missing_fields.append("recipient_name")
      if not rough_message:
        missing_fields.append("rough_message")
      
      # Return error if fields are missing
      if missing_fields:
        return "", f"Missing required information: {', '.join(missing_fields)}"
      
      # Generate professional email structure
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

  @staticmethod
  def review_email(input_data):
    """Display email for review and get user confirmation before sending."""
    try:
      # Extract email components
      recipient_email = input_data.get("recipient_email", "")
      subject = input_data.get("subject", "")
      body = input_data.get("body", "")
      
      # Validate required fields
      if not recipient_email or not subject or not body:
        return "", "Missing required fields for review"
      
      # Display formatted preview
      print("\n" + "="*60)
      print("📧 EMAIL PREVIEW")
      print("="*60)
      print(f"📤 To: {recipient_email}")
      print(f"📋 Subject: {subject}")
      print("-"*60)
      print("📝 Body:")
      print(body)
      print("="*60)
      
      # Get user confirmation
      while True:
        print(f"\n\u001b[93mClaude\u001b[0m: Do you want to send this email? (y/n): ", end="")
        response = input().strip().lower()
        if response in ['y', 'yes']:
          return "Email approved - proceeding to send immediately", None
        elif response in ['n', 'no']:
          return "", "Email sending cancelled by user"
        else:
          print(f"\u001b[93mClaude\u001b[0m: Please enter 'y' for yes or 'n' for no")
      
    except Exception as e:
      return "", str(e)

  @staticmethod
  def send_email(input_data):
    """Send an email via SMTP."""
    try:
      # Extract email components
      recipient_email = input_data.get("recipient_email", "")
      subject = input_data.get("subject", "")
      body = input_data.get("body", "")
      
      # Validate required fields
      if not recipient_email or not subject or not body:
        return "", "Missing required fields for sending"
      
      # Get SMTP configuration from environment
      smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
      smtp_port = int(os.environ.get("SMTP_PORT", "587"))
      sender_email = os.environ.get("SENDER_EMAIL")
      sender_password = os.environ.get("SENDER_PASSWORD")
      sender_name = os.environ.get("SENDER_NAME", "Email Agent")
      
      # Check for required configuration
      if not sender_email or not sender_password:
        return "", "SMTP configuration missing. Please set environment variables."
      
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

# Tool definitions with schemas
generate_email_definition = ToolDefinition(
  name="generate_email",
  description="Generate a professional email from rough input. Requires recipient email, name, and rough message content.",
  input_schema={
    "type": "object",
    "properties": {
      "recipient_email": {
        "type": "string",
        "description": "Email address of the recipient"
      },
      "recipient_name": {
        "type": "string",
        "description": "Name of the recipient"
      },
      "rough_message": {
        "type": "string",
        "description": "Core message content"
      },
      "subject": {
        "type": "string",
        "description": "Email subject line"
      }
    },
    "required": ["recipient_email", "recipient_name", "rough_message"]
  },
  function=ToolDefinition.generate_email
)

review_email_definition = ToolDefinition(
  name="review_email",
  description="Display the email in a nice format and ask for user confirmation before sending.",
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
  function=ToolDefinition.review_email
)

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
  function=ToolDefinition.send_email
)

def main():
  # Load environment variables
  load_dotenv()
  
  # Get API key from environment
  api_key = os.environ.get("ANTHROPIC_API_KEY")
  if not api_key:
    print("Warning: ANTHROPIC_API_KEY environment variable not set")
    api_key = input("Please enter your Anthropic API key: ")
  
  # Initialize Anthropic client
  client = anthropic.Anthropic(api_key=api_key)
  
  # Define input function
  def get_user_message():
    try:
      return input(), True
    except (EOFError, KeyboardInterrupt):
      return "", False
  
  # Initialize tools
  tools = [
    generate_email_definition,
    review_email_definition,
    send_email_definition
  ]
  
  # Create and run agent
  agent = Agent(client, get_user_message, tools)
  
  try:
    agent.run()
  except Exception as e:
    print(f"Error: {str(e)}")

if __name__ == "__main__":
  main()