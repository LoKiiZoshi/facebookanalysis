Facebook Page Analysis Django Project
Overview
This Django project fetches and analyzes posts from a public Facebook page using the Facebook Graph API. It stores post data (e.g., message, likes, comments) in a database and displays metrics like post frequency and engagement.
Features

Fetches posts from a specified Facebook page.
Stores post data (ID, message, created time, likes, comments) in a Django model.
Displays posts in a table with Bootstrap styling.
Basic analysis of post frequency by date.
Extensible for sentiment analysis or visualizations.

Prerequisites

Python 3.x
Django (pip install django)
Facebook Graph API library (pip install python-facebook-api)
Pandas for data analysis (pip install pandas)
Facebook Developer App with App ID, App Secret, and Access Token
Permissions: pages_read_engagement, pages_show_list

Setup

Clone the repository:git clone <repository-url>
cd facebook_analysis


Install dependencies:pip install -r requirements.txt


Configure environment variables in facebook_analysis/settings.py:FACEBOOK_APP_ID = 'your-app-id'
FACEBOOK_APP_SECRET = 'your-app-secret'
FACEBOOK_ACCESS_TOKEN = 'your-access-token'
FACEBOOK_PAGE_ID = 'your-page-id'


Run migrations:python manage.py makemigrations
python manage.py migrate
Start the development server:python manage.py runserver
Add sentiment analysis using TextBlob or VADER.
Integrate Chart.js for visualizing post metrics.
Support user authentication via django-allauth for user-specific data.
