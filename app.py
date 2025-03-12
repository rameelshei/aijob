import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from openai import OpenAI
from flask import Flask, request, render_template_string, render_template
import os
import re
import io
import PyPDF2
import subprocess
import tempfile
import json
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API Keys
PROXYCURL_API_KEY = os.environ.get('PROXYCURL_API_KEY', '')

# Sample job risks dictionary (expand this with real data)
job_risks = {
    # Technology
    'Software Engineer': 0.5,
    'Software Developer': 0.5,
    'Web Developer': 0.6,
    'Frontend Developer': 0.55,
    'Backend Developer': 0.45,
    'Full Stack Developer': 0.5,
    'Mobile Developer': 0.5,
    'iOS Developer': 0.5,
    'Android Developer': 0.5,
    'DevOps Engineer': 0.4,
    'Site Reliability Engineer': 0.4,
    'Systems Administrator': 0.6,
    'Network Administrator': 0.6,
    'Database Administrator': 0.7,
    'IT Support': 0.8,
    'IT Specialist': 0.7,
    'Helpdesk': 0.9,
    'QA Engineer': 0.7,
    'QA Tester': 0.8,
    'Test Engineer': 0.7,
    'Security Engineer': 0.4,
    'Cybersecurity Analyst': 0.4,
    'Cloud Engineer': 0.5,
    'Cloud Architect': 0.3,
    'Solutions Architect': 0.3,
    'Technical Architect': 0.3,
    'CTO': 0.3,
    'Chief Technology Officer': 0.3,
    'VP of Engineering': 0.3,
    'Engineering Manager': 0.4,
    'Technical Lead': 0.4,
    'Tech Lead': 0.4,
    
    # Data
    'Data Scientist': 0.4,
    'Data Analyst': 0.6,
    'Data Engineer': 0.5,
    'Machine Learning Engineer': 0.3,
    'AI Researcher': 0.2,
    'Business Intelligence Analyst': 0.6,
    'Business Analyst': 0.7,
    'Data Entry Clerk': 0.9,
    'Data Entry Specialist': 0.9,
    
    # Design
    'Graphic Designer': 0.7,
    'UI Designer': 0.65,
    'UX Designer': 0.6,
    'UI/UX Designer': 0.65,
    'Product Designer': 0.6,
    'Web Designer': 0.7,
    'Visual Designer': 0.7,
    'Illustrator': 0.6,
    'Art Director': 0.5,
    'Creative Director': 0.4,
    
    # Management
    'Project Manager': 0.3,
    'Product Manager': 0.35,
    'Program Manager': 0.4,
    'Operations Manager': 0.5,
    'Office Manager': 0.7,
    'CEO': 0.2,
    'Chief Executive Officer': 0.2,
    'CFO': 0.4,
    'Chief Financial Officer': 0.4,
    'COO': 0.3,
    'Chief Operating Officer': 0.3,
    'Director': 0.3,
    'Vice President': 0.3,
    'Manager': 0.5,
    'Team Lead': 0.4,
    'Supervisor': 0.6,
    
    # Marketing
    'Marketing Manager': 0.4,
    'Marketing Specialist': 0.6,
    'Digital Marketing Specialist': 0.6,
    'SEO Specialist': 0.7,
    'Social Media Manager': 0.6,
    'Content Writer': 0.8,
    'Content Creator': 0.7,
    'Copywriter': 0.75,
    'Content Strategist': 0.6,
    'Brand Manager': 0.5,
    'Public Relations Specialist': 0.6,
    'Communications Specialist': 0.6,
    
    # Sales
    'Sales Representative': 0.7,
    'Sales Associate': 0.8,
    'Account Executive': 0.6,
    'Account Manager': 0.5,
    'Business Development Manager': 0.5,
    'Sales Manager': 0.5,
    'Customer Success Manager': 0.6,
    
    # HR
    'HR Manager': 0.5,
    'Human Resources Manager': 0.5,
    'HR Specialist': 0.7,
    'Human Resources Specialist': 0.7,
    'Recruiter': 0.7,
    'Talent Acquisition Specialist': 0.7,
    'HR Coordinator': 0.8,
    'Human Resources Coordinator': 0.8,
    
    # Finance
    'Accountant': 0.8,
    'Financial Analyst': 0.6,
    'Financial Advisor': 0.7,
    'Bookkeeper': 0.9,
    'Auditor': 0.7,
    'Tax Preparer': 0.9,
    'Investment Banker': 0.6,
    'Investment Analyst': 0.6,
    'Loan Officer': 0.8,
    'Insurance Agent': 0.8,
    
    # Healthcare
    'Doctor': 0.3,
    'Physician': 0.3,
    'Surgeon': 0.2,
    'Nurse': 0.4,
    'Registered Nurse': 0.4,
    'Nurse Practitioner': 0.3,
    'Medical Assistant': 0.6,
    'Pharmacist': 0.6,
    'Pharmacy Technician': 0.8,
    'Physical Therapist': 0.4,
    'Occupational Therapist': 0.4,
    'Dentist': 0.3,
    'Dental Hygienist': 0.5,
    'Veterinarian': 0.3,
    'Vet Tech': 0.6,
    
    # Education
    'Teacher': 0.5,
    'Professor': 0.4,
    'Tutor': 0.6,
    'School Administrator': 0.5,
    'Principal': 0.4,
    'Librarian': 0.7,
    'Research Assistant': 0.6,
    'Researcher': 0.4,
    
    # Legal
    'Lawyer': 0.6,
    'Attorney': 0.6,
    'Paralegal': 0.8,
    'Legal Assistant': 0.8,
    'Judge': 0.3,
    'Legal Counsel': 0.6,
    
    # Service Industry
    'Chef': 0.4,
    'Cook': 0.7,
    'Waiter': 0.9,
    'Waitress': 0.9,
    'Server': 0.9,
    'Bartender': 0.8,
    'Barista': 0.8,
    'Host': 0.9,
    'Hostess': 0.9,
    'Housekeeper': 0.9,
    'Janitor': 0.8,
    'Custodian': 0.8,
    'Cleaner': 0.9,
    'Security Guard': 0.8,
    'Receptionist': 0.9,
    'Customer Service Representative': 0.9,
    'Customer Support': 0.85,
    'Call Center Agent': 0.95,
    
    # Transportation
    'Truck Driver': 0.9,
    'Delivery Driver': 0.9,
    'Uber Driver': 0.95,
    'Lyft Driver': 0.95,
    'Taxi Driver': 0.95,
    'Bus Driver': 0.9,
    'Pilot': 0.6,
    'Flight Attendant': 0.7,
    
    # Retail
    'Retail Worker': 0.9,
    'Retail Associate': 0.9,
    'Cashier': 0.95,
    'Store Manager': 0.7,
    'Store Associate': 0.9,
    'Sales Clerk': 0.9,
    
    # Creative
    'Photographer': 0.6,
    'Videographer': 0.5,
    'Video Editor': 0.6,
    'Film Editor': 0.6,
    'Actor': 0.4,
    'Actress': 0.4,
    'Musician': 0.4,
    'Writer': 0.6,
    'Journalist': 0.7,
    'Reporter': 0.7,
    'Editor': 0.6,
    
    # Trades
    'Electrician': 0.5,
    'Plumber': 0.5,
    'Carpenter': 0.6,
    'Construction Worker': 0.7,
    'Mechanic': 0.6,
    'HVAC Technician': 0.6,
    'Welder': 0.7,
    'Machinist': 0.8,
    'Factory Worker': 0.9,
    'Assembly Line Worker': 0.95,
    
    # Miscellaneous
    'Consultant': 0.5,
    'Freelancer': 0.6,
    'Contractor': 0.7,
    'Analyst': 0.6,
    'Specialist': 0.7,
    'Coordinator': 0.8,
    'Assistant': 0.9,
    'Intern': 0.8,
    'Student': 0.7
}

# Add startup-specific job titles to the job_risks dictionary
startup_jobs = {
    # Startup Leadership
    'Founder': 0.3,
    'Co-Founder': 0.3,
    'Startup CEO': 0.25,
    'Startup CTO': 0.3,
    'Technical Co-Founder': 0.3,
    'Non-Technical Co-Founder': 0.4,
    'Founding Engineer': 0.4,
    'Chief Product Officer': 0.35,
    'Chief Revenue Officer': 0.4,
    'Chief Marketing Officer': 0.45,
    'Chief Growth Officer': 0.4,
    'Chief of Staff': 0.5,
    'VP of Product': 0.4,
    'Head of Product': 0.4,
    'VP of Engineering': 0.35,
    'Head of Engineering': 0.35,
    'VP of Design': 0.5,
    'Head of Design': 0.5,
    'VP of Sales': 0.4,
    'Head of Sales': 0.4,
    'VP of Marketing': 0.45,
    'Head of Marketing': 0.45,
    'VP of Operations': 0.5,
    'Head of Operations': 0.5,
    'VP of People': 0.6,
    'Head of People': 0.6,
    'VP of Customer Success': 0.5,
    'Head of Customer Success': 0.5,
    'VP of Business Development': 0.4,
    'Head of Business Development': 0.4,
    
    # Startup-specific roles
    'Growth Hacker': 0.6,
    'Growth Marketer': 0.6,
    'Product Manager': 0.4,
    'Product Owner': 0.4,
    'Scrum Master': 0.7,
    'DevOps Engineer': 0.5,
    'Full Stack Developer': 0.5,
    'Frontend Engineer': 0.55,
    'Backend Engineer': 0.45,
    'Mobile Developer': 0.5,
    'UI/UX Designer': 0.6,
    'Product Designer': 0.55,
    'Customer Success Manager': 0.6,
    'Community Manager': 0.7,
    'Content Marketer': 0.7,
    'SEO Specialist': 0.8,
    'SEM Specialist': 0.8,
    'Paid Acquisition Manager': 0.7,
    'Venture Capital Associate': 0.6,
    'Venture Capital Analyst': 0.7,
    'Angel Investor': 0.3,
    'Startup Advisor': 0.4,
    'Startup Mentor': 0.3,
    'Startup Coach': 0.4,
    'Pitch Deck Consultant': 0.7,
    'Startup Recruiter': 0.7,
    'Technical Recruiter': 0.7,
}

# Add startup jobs to the main job_risks dictionary
job_risks.update(startup_jobs)

# Set up OpenAI API using environment variable
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))

# Function to extract information from resume text
def extract_resume_info(text):
    """
    Extracts name, job title, and skills from resume text.
    Uses simple pattern matching and OpenAI for extraction.
    """
    try:
        # Check if we have enough text to analyze
        if not text or len(text.strip()) < 50:
            print("Resume text is too short or empty")
            return {
                'name': 'Unknown',
                'job_title': 'Unknown',
                'company': 'Unknown',
                'skills': ['No skills found']
            }
            
        # Use OpenAI to extract structured information from the resume
        prompt = (
            "Extract the following information from this resume text. "
            "If you can't find something, make a reasonable guess based on the context:\n\n"
            "1. Full Name\n"
            "2. Current or Most Recent Job Title\n"
            "3. Current or Most Recent Company\n"
            "4. List of Skills (technical and soft skills)\n\n"
            f"Resume text:\n{text[:4000]}"  # Limit text to 4000 chars to stay within token limits
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a resume parser that extracts structured information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        parsed_text = response.choices[0].message.content
        print(f"Parsed resume information: {parsed_text}")
        
        # Extract information from the AI response
        name_match = re.search(r"(?:Full Name|Name):?\s*(.*?)(?:\n|$)", parsed_text, re.IGNORECASE)
        job_match = re.search(r"(?:Job Title|Title|Position):?\s*(.*?)(?:\n|$)", parsed_text, re.IGNORECASE)
        company_match = re.search(r"(?:Company|Employer|Organization):?\s*(.*?)(?:\n|$)", parsed_text, re.IGNORECASE)
        skills_match = re.search(r"(?:Skills|Abilities):?\s*(.*?)(?:\n\n|$)", parsed_text, re.DOTALL | re.IGNORECASE)
        
        name = name_match.group(1).strip() if name_match else "Unknown"
        job_title = job_match.group(1).strip() if job_match else "Unknown"
        company = company_match.group(1).strip() if company_match else "Unknown"
        
        if skills_match:
            skills_text = skills_match.group(1).strip()
            # Split skills by commas, bullets, or newlines
            skills = [s.strip() for s in re.split(r'[,•\n-]+', skills_text) if s.strip()]
        else:
            skills = ["No skills found"]
        
        return {
            'name': name,
            'job_title': job_title,
            'company': company,
            'skills': skills
        }
    except Exception as e:
        print(f"Error extracting resume info: {e}")
        # Return default values on error
        return {
            'name': 'Error processing resume',
            'job_title': 'Unknown',
            'company': 'Unknown',
            'skills': ['Error processing skills']
        }

# Function to assess automation risk
def get_automation_risk(job_title):
    """
    Matches job title to automation risk using fuzzy matching.
    Returns risk as a percentage.
    """
    # Clean the job title for better matching
    cleaned_job_title = job_title.lower().strip()
    
    # Try exact match first
    for key in job_risks:
        if key.lower() == cleaned_job_title:
            return job_risks[key] * 100
    
    # If no exact match, try fuzzy matching
    best_match = process.extractOne(cleaned_job_title, job_risks.keys())
    
    # Lower threshold to 70% for more matches
    if best_match and best_match[1] > 70:
        return job_risks[best_match[0]] * 100
    
    # If still no match, try matching on parts of the job title
    words = cleaned_job_title.split()
    if len(words) > 1:
        for word in words:
            if len(word) > 3:  # Only consider meaningful words
                word_match = process.extractOne(word, job_risks.keys())
                if word_match and word_match[1] > 80:
                    return job_risks[word_match[0]] * 100
    
    # Default risk if no match found (medium risk)
    print(f"No match found for job title: {job_title}")
    return 50.0

# Function to generate a humorous roast
def generate_roast(profile_info, risk, has_profile_pic=False):
    """
    Uses OpenAI API to generate a funny roast based on profile and risk.
    """
    # Determine if this is likely a startup executive/manager
    is_startup_exec = False
    startup_keywords = ['founder', 'ceo', 'cto', 'chief', 'head of', 'vp', 'director', 'lead', 'startup', 'venture']
    
    for keyword in startup_keywords:
        if keyword.lower() in profile_info['job_title'].lower() or keyword.lower() in profile_info['company'].lower():
            is_startup_exec = True
            break
    
    # Calculate human spark factor (inverse of risk, but with some randomness)
    # For demo purposes, we'll use a formula that gives higher spark to lower risk jobs
    # but with some variation
    random_factor = random.uniform(-15, 15)  # Random value between -15 and 15
    human_spark = 100 - risk + random_factor
    # Ensure human_spark stays within 0-100 range
    human_spark = max(5, min(95, human_spark))
    
    # Determine which quadrant the user is in
    quadrant = ""
    if risk < 50 and human_spark >= 50:
        quadrant = "Robot-Proof Creative"
    elif risk >= 50 and human_spark >= 50:
        quadrant = "Endangered Innovator"
    elif risk < 50 and human_spark < 50:
        quadrant = "Safe but Dull"
    else:
        quadrant = "Prime Robot Bait"
    
    # Add profile picture context if available
    profile_pic_context = ""
    if has_profile_pic:
        profile_pic_context = "The person also has a LinkedIn profile picture. Feel free to make a light-hearted joke about professional headshots or LinkedIn profile pictures in general, but don't be mean about their appearance."
    
    # Add quadrant-specific context
    quadrant_context = f"Based on our analysis, this person falls into the '{quadrant}' quadrant of our AI replacement matrix. "
    
    if quadrant == "Robot-Proof Creative":
        quadrant_context += "This means they have high creative value but low automation risk. Roast them about being safe from AI but perhaps overconfident about their creative abilities."
    elif quadrant == "Endangered Innovator":
        quadrant_context += "This means they have high creative value but also high automation risk. Roast them about being innovative in a field that's rapidly being automated."
    elif quadrant == "Safe but Dull":
        quadrant_context += "This means they have low creative value but also low automation risk. Roast them about having a safe but incredibly boring job that even AI doesn't want."
    else:  # Prime Robot Bait
        quadrant_context += "This means they have low creative value and high automation risk. Roast them about being in the perfect position to be replaced by AI."
    
    if is_startup_exec:
        prompt = (
            "You are a comedy writer with a dry, sarcastic style tasked with roasting a startup executive based on their resume.\n"
            "Your roast should be witty, observational, and subtly sarcastic. Avoid flowery language, metaphors, and over-the-top humor.\n"
            "Keep it light-hearted and non-offensive, but make it specifically relevant to startup culture and the tech industry.\n"
            "Include references to one or two of these topics: burnout, pivoting, disruption, innovation, 'move fast and break things', venture capital, pitch decks, product-market fit, scaling, unicorns, failed IPOs, over-valuation, WeWork-style downfalls, startup buzzwords, AI hype, crypto crashes, endless funding rounds, or 'we're like Uber but for X'.\n"
            f"{profile_pic_context}\n"
            f"{quadrant_context}\n"
            "Here's the info:\n"
            f"- Name: {profile_info['name']}\n"
            f"- Job Title: {profile_info['job_title']}\n"
            f"- Company: {profile_info['company']}\n"
            f"- Skills: {', '.join(profile_info['skills'])}\n"
            f"- Automation Risk: {risk}%\n"
            f"- Human Spark Factor: {human_spark:.1f}%\n"
            f"- Matrix Quadrant: {quadrant}\n\n"
            "Write a short, satirical roast (150-200 characters) focusing on their job's automation risk and their position in the matrix quadrant.\n"
            "IMPORTANT: Ensure your response is a complete paragraph with full sentences and proper punctuation. Do not end mid-sentence.\n"
            "Make it shareable and quotable for social media. Be direct, concise, and avoid unnecessary flourishes."
        )
    else:
        prompt = (
            "You are a comedy writer with a dry, sarcastic style tasked with roasting someone based on their resume.\n"
            "Your roast should be witty, observational, and subtly sarcastic. Avoid flowery language, metaphors, and over-the-top humor.\n"
            "Keep it light-hearted and non-offensive, but make it specifically relevant to corporate culture and office life.\n"
            "Include references to one or two of these topics: endless meetings, corporate buzzwords, office politics, performance reviews, middle management, email overload, corporate jargon, pointless KPIs, outdated technology, open office plans, work-life balance, corporate retreats, team building exercises, LinkedIn humble-brags, or corporate restructuring.\n"
            f"{profile_pic_context}\n"
            f"{quadrant_context}\n"
            "Here's the info:\n"
            f"- Name: {profile_info['name']}\n"
            f"- Job Title: {profile_info['job_title']}\n"
            f"- Company: {profile_info['company']}\n"
            f"- Skills: {', '.join(profile_info['skills'])}\n"
            f"- Automation Risk: {risk}%\n"
            f"- Human Spark Factor: {human_spark:.1f}%\n"
            f"- Matrix Quadrant: {quadrant}\n\n"
            "Write a short, satirical roast (150-200 characters) focusing on their job's automation risk and their position in the matrix quadrant.\n"
            "IMPORTANT: Ensure your response is a complete paragraph with full sentences and proper punctuation. Do not end mid-sentence.\n"
            "Make it shareable and quotable for social media. Be direct, concise, and avoid unnecessary flourishes."
        )
    
    try:
        # Use chat completions API instead of completions for better reliability
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a comedy writer who specializes in dry humor, sarcasm, and observational comedy about workplace and technology."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7,
            presence_penalty=0.4,  # Moderate uniqueness
            frequency_penalty=0.5   # Moderate repetition prevention
        )
        
        roast = response.choices[0].message.content.strip()
        
        # Ensure the roast ends with a complete sentence
        if not roast.endswith('.') and not roast.endswith('!') and not roast.endswith('?'):
            roast += '.'
            
        return roast
        
    except Exception as e:
        # Fallback in case of API errors
        print(f"Error generating roast: {str(e)}")
        return f"Congratulations {profile_info['name']}, your job has a {risk}% chance of being automated! Even our roasting algorithm crashed trying to process your career choices. That's either very good or very bad news."

# Function to extract text from PDF using pdftotext if available
def extract_text_from_pdf_fallback(pdf_path):
    """Try to extract text from PDF using external tools if PyPDF2 fails"""
    try:
        # Try using pdftotext if available (part of poppler-utils)
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_txt:
            try:
                subprocess.run(['pdftotext', pdf_path, temp_txt.name], check=True, capture_output=True)
                with open(temp_txt.name, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except (subprocess.SubprocessError, FileNotFoundError):
                # pdftotext not available or failed
                pass
        
        # If we get here, both methods failed
        return None
    except Exception as e:
        print(f"Fallback PDF extraction error: {str(e)}")
        return None

# Function to extract text from PDF using direct binary reading as last resort
def extract_text_direct(pdf_path):
    """Extract text directly from PDF by looking for text markers in binary"""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
        
        # Convert binary to string with replacement for non-decodable bytes
        text = content.decode('utf-8', errors='replace')
        
        # Clean up the text by removing non-printable characters
        cleaned_text = ''.join(c if c.isprintable() or c in '\n\t ' else ' ' for c in text)
        
        # Remove binary garbage by keeping only reasonable line lengths
        lines = cleaned_text.split('\n')
        filtered_lines = [line for line in lines if len(line) < 1000 and len(line) > 3]
        
        return '\n'.join(filtered_lines)
    except Exception as e:
        print(f"Direct text extraction error: {str(e)}")
        return None

# Function to extract LinkedIn profile data using Proxycurl API
def extract_linkedin_profile(linkedin_url):
    """
    Extract LinkedIn profile data using Proxycurl API
    """
    try:
        print(f"Attempting to extract LinkedIn profile for URL: {linkedin_url}")
        
        headers = {'Authorization': 'Bearer ' + PROXYCURL_API_KEY}
        api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
        params = {
            'linkedin_profile_url': linkedin_url,
            'extra': 'include',
            'skills': 'include',
            'use_cache': 'if-present',
            'fallback_to_cache': 'on-error',
        }
        
        print(f"Making API request to: {api_endpoint}")
        print(f"With params: {params}")
        
        response = requests.get(api_endpoint, params=params, headers=headers)
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # Print the raw response for debugging
                print(f"Raw response content type: {type(response.text)}")
                print(f"Raw response content (first 200 chars): {response.text[:200]}...")
                
                profile_data = response.json()
                print(f"Successfully parsed JSON response")
                print(f"Response data type: {type(profile_data)}")
                
                # Check if profile_data is a dictionary
                if not isinstance(profile_data, dict):
                    print(f"Unexpected response format: {type(profile_data)}")
                    return None
                
                # Print some keys from the response for debugging
                print(f"Response keys: {list(profile_data.keys())[:10] if isinstance(profile_data, dict) else 'Not a dictionary'}")
                
                # Extract relevant information
                first_name = profile_data.get('first_name', '')
                last_name = profile_data.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                
                # If name is empty, try to get it from other fields
                if not full_name:
                    full_name = profile_data.get('full_name', 'Unknown')
                
                print(f"Extracted name: {full_name}")
                
                job_title = profile_data.get('occupation', 'Unknown')
                print(f"Extracted job title: {job_title}")
                
                # Get current company from experiences
                company = "Unknown"
                experiences = profile_data.get('experiences', [])
                print(f"Experiences type: {type(experiences)}")
                print(f"Experiences count: {len(experiences) if isinstance(experiences, list) else 'Not a list'}")
                
                if experiences and isinstance(experiences, list) and len(experiences) > 0:
                    # Find the current job (no end date)
                    current_jobs = [exp for exp in experiences if isinstance(exp, dict) and not exp.get('ends_at')]
                    if current_jobs:
                        company = current_jobs[0].get('company', 'Unknown')
                    else:
                        # If no current job found, use the most recent
                        company = experiences[0].get('company', 'Unknown')
                
                print(f"Extracted company: {company}")
                
                # Extract skills
                skills = []
                skills_data = profile_data.get('skills', [])
                print(f"Skills data type: {type(skills_data)}")
                print(f"Skills count: {len(skills_data) if isinstance(skills_data, list) else 'Not a list'}")
                
                if skills_data and isinstance(skills_data, list):
                    skills = [skill.get('name', '') for skill in skills_data if isinstance(skill, dict) and skill.get('name')]
                
                # If no skills found, add some default skills
                if not skills:
                    skills = ["Professional networking", "Communication", "Industry knowledge"]
                
                print(f"Extracted skills: {skills[:5]}...")
                
                # Get profile picture URL if available
                profile_pic_url = profile_data.get('profile_pic_url', None)
                print(f"Profile picture URL available: {profile_pic_url is not None}")
                
                result = {
                    'name': full_name,
                    'job_title': job_title,
                    'company': company,
                    'skills': skills,
                    'profile_pic_url': profile_pic_url,
                    'raw_data': profile_data  # Store the raw data for additional info if needed
                }
                
                print(f"Successfully extracted LinkedIn profile data")
                return result
            except Exception as e:
                print(f"Error parsing LinkedIn profile data: {str(e)}")
                print(f"Response content: {response.text[:500]}...")  # Print first 500 chars of response
                return None
        else:
            print(f"Failed to retrieve LinkedIn profile. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error extracting LinkedIn profile: {str(e)}")
        return None

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(file):
    """
    Extract text from a PDF file using PyPDF2 with fallback methods.
    """
    # Save the file temporarily
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.pdf')
    file.save(temp_path)
    
    try:
        # Try primary method first (PyPDF2)
        resume_text = ""
        with open(temp_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    resume_text += page_text + "\n"
        
        # If primary method didn't extract enough text, try fallback
        if len(resume_text.strip()) < 50:
            print("Primary PDF extraction yielded insufficient text, trying fallback...")
            fallback_text = extract_text_from_pdf_fallback(temp_path)
            if fallback_text and len(fallback_text.strip()) > len(resume_text.strip()):
                resume_text = fallback_text
                print("Using fallback PDF extraction method")
        
        # If still not enough text, try direct extraction as last resort
        if len(resume_text.strip()) < 50:
            print("Fallback PDF extraction failed or yielded insufficient text, trying direct extraction...")
            direct_text = extract_text_direct(temp_path)
            if direct_text:
                resume_text = direct_text
                print("Using direct text extraction method")
    except Exception as e:
        # Try fallback method if primary fails
        print(f"Primary PDF extraction failed: {str(e)}, trying fallback...")
        resume_text = extract_text_from_pdf_fallback(temp_path) or ""
        
        # If fallback also fails, try direct extraction as last resort
        if not resume_text or len(resume_text.strip()) < 50:
            print("Fallback PDF extraction failed or yielded insufficient text, trying direct extraction...")
            direct_text = extract_text_direct(temp_path)
            if direct_text:
                resume_text = direct_text
                print("Using direct text extraction method")
    
    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    if not resume_text or len(resume_text.strip()) < 50:
        raise Exception("Could not extract sufficient text from the PDF file")
    
    return resume_text

# Flask route for the app
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if LinkedIn URL was submitted
        linkedin_url = request.form.get('linkedin_url')
        if linkedin_url and linkedin_url.strip():
            try:
                # Extract profile information from LinkedIn
                profile_info = extract_linkedin_profile(linkedin_url.strip())
                
                if profile_info:
                    # Get job title and assess risk
                    job_title = profile_info['job_title']
                    risk = get_automation_risk(job_title)
                    
                    # Check if profile has a picture
                    has_profile_pic = profile_info.get('profile_pic_url') is not None
                    
                    # Generate roast
                    roast = generate_roast(profile_info, risk, has_profile_pic)
                    
                    return render_template('result.html', 
                                          name=profile_info['name'],
                                          job_title=job_title, 
                                          company=profile_info['company'],
                                          skills=profile_info['skills'],
                                          risk=risk,
                                          roast=roast)
                else:
                    return render_template('index.html', error="Could not extract profile information from the LinkedIn URL.")
            except Exception as e:
                print(f"Error processing LinkedIn URL: {str(e)}")
                return render_template('index.html', error=f"Error processing LinkedIn URL: {str(e)}")
        
        # Check if file was uploaded
        elif 'resume' in request.files:
            file = request.files['resume']
            
            if file.filename == '':
                return render_template('index.html', error="No file selected")
            
            if file:
                try:
                    # Process the file based on its type
                    if file.filename.endswith('.pdf'):
                        text = extract_text_from_pdf(file)
                    else:
                        # Read text file content
                        text = file.read().decode('utf-8', errors='ignore')
                    
                    # Check if we got enough text
                    if len(text) < 50:
                        return render_template('index.html', error="Could not extract sufficient text from the file. Please try a different file or format.")
                    
                    # Extract information from resume
                    profile_info = extract_resume_info(text)
                    
                    # Get job title and assess risk
                    job_title = profile_info['job_title']
                    risk = get_automation_risk(job_title)
                    
                    # Generate roast (no profile pic for resume uploads)
                    roast = generate_roast(profile_info, risk, False)
                    
                    return render_template('result.html', 
                                          name=profile_info['name'],
                                          job_title=job_title, 
                                          company=profile_info['company'],
                                          skills=profile_info['skills'],
                                          risk=risk,
                                          roast=roast)
                except Exception as e:
                    print(f"Error processing file: {str(e)}")
                    return render_template('index.html', error=f"Error processing file: {str(e)}")
        
        # If neither LinkedIn URL nor file was provided
        return render_template('index.html', error="Please provide a LinkedIn URL or upload a resume file")
    
    return render_template('index.html')

# Retro-style HTML template with sharing buttons
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will AI Replace You? | Startup Edition</title>
    <meta property="og:title" content="Will AI Replace Me? | Startup Edition">
    <meta property="og:description" content="I just found out my job has a {{ risk }}% chance of being automated. Check your own job's AI risk!">
    <meta property="og:image" content="https://placehold.co/600x400/000000/00ff00?text=AI+Risk:+{{ risk }}%">
    <meta name="twitter:card" content="summary_large_image">
    <style>
        body {
            background-color: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            text-align: center;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            border: 2px solid #0f0;
            padding: 20px;
        }
        .risk-meter {
            width: 100%;
            height: 20px;
            background: #333;
            position: relative;
            margin: 10px 0;
        }
        .risk-bar {
            height: 100%;
            background: #f00;
            width: {{ risk }}%;
        }
        .roast {
            margin-top: 20px;
            padding: 10px;
            border: 1px dashed #0f0;
            text-align: left;
        }
        h1 {
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .back-button {
            margin-top: 20px;
        }
        .back-button a {
            color: #0f0;
            text-decoration: none;
            border: 1px solid #0f0;
            padding: 5px 10px;
        }
        .share-container {
            margin-top: 30px;
            padding: 15px;
            border: 1px dashed #0f0;
        }
        .share-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 15px;
        }
        .share-button {
            background: #0f0;
            color: #000;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            text-decoration: none;
            display: inline-block;
        }
        .share-text {
            background: #111;
            color: #0f0;
            border: 1px solid #0f0;
            padding: 10px;
            margin: 10px 0;
            text-align: left;
            font-size: 14px;
        }
        .startup-badge {
            display: inline-block;
            background: #0f0;
            color: #000;
            padding: 5px 10px;
            margin-top: 10px;
            font-weight: bold;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Will AI Replace You?</h1>
        <div class="startup-badge">STARTUP EDITION</div>
        <h2>Profile Scan</h2>
        <p><strong>Name:</strong> {{ profile.name }}</p>
        <p><strong>Job Title:</strong> {{ profile.job_title }}</p>
        <p><strong>Company:</strong> {{ profile.company }}</p>
        <p><strong>Skills:</strong> {{ profile.skills | join(', ') }}</p>
        <h2>Automation Risk: {{ risk }}%</h2>
        <div class="risk-meter">
            <div class="risk-bar"></div>
        </div>
        <div class="roast">
            <h3>Your AI-Powered Roast</h3>
            <p>{{ roast }}</p>
        </div>
        
        <div class="share-container">
            <h3>Share Your Results</h3>
            <div class="share-text">
                🤖 My job ({{ profile.job_title }}) has a {{ risk }}% chance of being automated by AI!
                
                {{ roast }}
                
                Check your own job's AI risk at willaireplaceyo.us
                #AIrisk #StartupLife
            </div>
            <div class="share-buttons">
                <a class="share-button" href="https://twitter.com/intent/tweet?text={{ 'My job (' + profile.job_title + ') has a ' + risk|string + '%25 chance of being automated by AI! Check your own job\'s AI risk at willaireplaceyo.us %23AIrisk %23StartupLife'|urlencode }}" target="_blank">Share on X</a>
                <a class="share-button" href="https://www.linkedin.com/sharing/share-offsite/?url=https://willaireplaceyo.us" target="_blank">Share on LinkedIn</a>
            </div>
        </div>
        
        <div class="back-button">
            <a href="/">Try Another</a>
        </div>
    </div>
</body>
</html>
'''

# Run the app
if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    # Run the app, binding to all interfaces (0.0.0.0) for production
    app.run(host="0.0.0.0", port=port, debug=False)