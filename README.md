# Email Agent

A simple AI-powered email agent that can generate professional emails and send them via SMTP.

## Setup

1. Install dependencies:
   ```bash
   pipenv install
   ```

2. Set up your environment configuration:
   ```bash
   # Copy the template
   cp env.example .env
   
   # Edit .env with your actual values
   # Or create .env.local to override specific settings
   ```

3. For Gmail users:
   - Enable 2-factor authentication
   - Generate an "App Password" instead of using your regular password
   - Use the app password as `SENDER_PASSWORD`

## Usage

Run the agent:
```bash
pipenv run python email_agent.py
```

## Available Tools

- **generate_email**: Creates professional emails from rough input
- **review_email**: Shows email preview and asks for confirmation
- **send_email**: Sends emails via SMTP (only after review approval)

## Email Workflow

1. **Generate**: AI creates professional email from your rough input
2. **Review**: You see a nice preview and approve/reject before sending
3. **Send**: Email is sent only after your approval

## Example Interactions

- "Generate an email to john@example.com named John asking about the project status"
- "Send an email to jane@example.com with subject 'Meeting Tomorrow' and body 'Hi Jane, just confirming our meeting tomorrow at 2pm.'"
