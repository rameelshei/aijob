# Does My Job Exist in Five Years?

A Skynet-themed career assessment tool that analyzes LinkedIn profiles to determine the risk of AI automation.

## Features

- LinkedIn profile analysis
- AI risk assessment for various job roles
- Humorous AI-generated "roasts" about your career prospects
- Interactive Human Survival Matrix
- Social sharing capabilities

## Deployment Instructions

### Prerequisites

- Python 3.9+
- pip
- A web hosting service (Heroku, Render, DigitalOcean, etc.)
- Domain name (doesmyjobexistinfiveyears.com)

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python app.py`
6. Visit `http://localhost:8000` in your browser

### Production Deployment

#### Heroku Deployment

1. Create a Heroku account and install the Heroku CLI
2. Login to Heroku: `heroku login`
3. Create a new Heroku app: `heroku create doesmyjobexistinfiveyears`
4. Push to Heroku: `git push heroku main`
5. Set environment variables:
   ```
   heroku config:set PROXYCURL_API_KEY=your_api_key
   ```
6. Open the app: `heroku open`

#### Render Deployment

1. Create a Render account
2. Connect your GitHub repository
3. Create a new Web Service
4. Select the repository
5. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. Set environment variables
7. Deploy

### Domain Configuration

1. Purchase the domain (doesmyjobexistinfiveyears.com)
2. Configure DNS settings to point to your hosting provider
3. Set up SSL certificate for secure HTTPS connections

## Maintenance

- Regularly update dependencies
- Monitor API usage (Proxycurl)
- Back up data regularly

## License

All rights reserved. This project is proprietary and confidential.

© 2025 The Bottleneck 