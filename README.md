# Welcome to  OneTracker's official Backend  

## Project info


**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected.

The only requirement is having Python 3.12 & poetry installed - [install with pip](https://install.python-poetry.org)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone https://github.com/Sidd07Dev/onetracker-backend

# Step 2: Navigate to the project directory.
cd onetracker-backend

# Step 3: add below keys in .env file
PORT = 8000
DB_URI = ******

CORS_ORIGIN = *

SMTP_HOST=******
SMTP_PORT=****
SMTP_USER=****
SMTP_PASS=****
COMPANY_EMAIL=****


CF_ACCOUNT_ID=****
CF_API_TOKEN=****
VECTORIZE_INDEX_NAME=onetracker-knowledge


API_KEY = ******


REDIS_DB_URI = *******

# Step 4: Install the necessary dependencies.
poetry install


# Step 5: Start the development server with auto-reloading and an instant preview.
poetry run dev

# Step 6: After Start the development server pase the below url in browser.
http://localhost:8000
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Python 3.12
- FastAPI
- Poetry
- Cloudflare Worker AI (llama3)
- Cloudflare Worker(Vectorize)
- postgreSql
- Redis




# Onetraker
