# Email Agent - Setup Instructions

A simple AI-powered email agent that can generate professional emails and send them via SMTP. This guide will walk you through setting up your development environment and configuring all necessary services.

## Prerequisites

### Python 3.11+ Installation

Our agent requires Python 3.11 or higher. To check your Python version:

```bash
python --version
# or
python3 --version
```

If you need to install or upgrade Python:
- **Windows**: Download from [python.org](https://python.org) and check "Add Python to PATH" during installation
- **macOS**: Use Homebrew (`brew install python@3.11`) or download from python.org
- **Linux**: Use your package manager (e.g., `sudo apt install python3.11` for Ubuntu/Debian)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ferdelamad/email_agent.git
cd email_agent
```

### 2. Install Dependencies

We use Pipenv for dependency management. First, install Pipenv if you don't have it:

```bash
pip install pipenv
# or
pip3 install pipenv
```

Then install project dependencies:

```bash
pipenv install
pipenv shell  # Activate the virtual environment
```

> **Alternative**: If you prefer using `venv` and `pip`:
> ```bash
> python -m venv venv
> source venv/bin/activate  # On Windows: venv\Scripts\activate
> pip install anthropic python-dotenv
> ```

### 3. Get Your Anthropic API Key

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Click "Get API Key" on the main page
4. Create a new key with a descriptive name
5. Copy the key immediately (you won't see it again)

### 4. Configure Gmail SMTP Access

Gmail requires app-specific passwords for SMTP when 2-Step Verification is enabled.

#### Enable 2-Step Verification

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google," find "2-Step Verification"
3. Follow the setup process with your phone number

#### Generate App Password

1. Return to [Security settings](https://myaccount.google.com/security)
2. Under "How you sign in to Google," select "2-Step Verification"
3. Scroll to the bottom and click "App passwords"
   - If not visible, search for "App passwords" in the top search bar
4. Re-authenticate if prompted
5. Enter a custom name like "Email Agent" in the text field
6. Click "Create"
7. Copy the 16-character password (remove spaces when using it)

### 5. Configure Environment Variables

Copy the environment template:

```bash
cp env.example .env
```

Edit `.env` with your values:

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# SMTP Email Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your16charapppass  # No spaces!
SENDER_NAME=Your Name

# SMTP Server Settings (Gmail defaults)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Important**: 
- Never commit `.env` to version control
- Remove spaces from the app password
- Use your full Gmail address

### 6. Test Your Setup

Run the test script to verify everything works:

```bash
python test_email.py
```

Select option 1 to send a test email. If successful, you'll receive an email within seconds.

### 7. Running the Agent

Starting the agent is straightforward:

```bash
python email_agent.py
```

Once running, you can interact with the agent naturally. Try requests like: 

```bash
"Send an email to my_email@domain.com telling him about our meeting tomorrow" 
```

And watch as the agent generates the email, shows you a preview, and waits for your approval before sending.

The agent will guide you through any missing information and handle errors gracefully. If something isn't working as expected, check that your SMTP credentials are properly configured and that your API key is set correctly.

## Troubleshooting

### Authentication Failed
- Verify 2-Step Verification is enabled
- Ensure you're using the app password (not your Gmail password)
- Check the app password has no spaces

### Connection Timeout
- Check internet connection
- Verify firewall allows port 587
- Some corporate networks block SMTP

### Missing Environment Variables
- Ensure `.env` is in the project root
- Check variable names are exact (case-sensitive)
- Remove spaces around `=` signs

## Project Structure

```
email_agent/
├── email_agent.py    # Main agent implementation
├── test_email.py     # SMTP configuration tester
├── env.example       # Environment variable template
├── .env              # Your configuration (create this)
├── Pipfile           # Python dependencies
└── Pipfile.lock      # Locked dependency versions
```

## Support

If you encounter issues, please check:
1. All environment variables are correctly set
2. Your Gmail account has 2-Step Verification enabled
3. You're using the app password (not your regular password)
4. Python version is 3.11 or higher

For additional help, please open an issue on GitHub.
