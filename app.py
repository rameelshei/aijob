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
    'Software Engineer': 0.7,
    'Software Developer': 0.7,
    'Web Developer': 0.8,
    'Frontend Developer': 0.75,
    'Backend Developer': 0.65,
    'Full Stack Developer': 0.7,
    'Mobile Developer': 0.7,
    'iOS Developer': 0.7,
    'Android Developer': 0.7,
    'DevOps Engineer': 0.6,
    'Site Reliability Engineer': 0.6,
    'Systems Administrator': 0.8,
    'Network Administrator': 0.8,
    'Database Administrator': 0.9,
    'IT Support': 0.95,
    'IT Specialist': 0.9,
    'Helpdesk': 0.95,
    'QA Engineer': 0.85,
    'QA Tester': 0.9,
    'Test Engineer': 0.85,
    'Security Engineer': 0.6,
    'Cybersecurity Analyst': 0.6,
    'Cloud Engineer': 0.7,
    'Cloud Architect': 0.5,
    'Solutions Architect': 0.5,
    'Technical Architect': 0.5,
    'CTO': 0.5,
    'Chief Technology Officer': 0.5,
    'VP of Engineering': 0.5,
    'Engineering Manager': 0.6,
    'Technical Lead': 0.6,
    'Tech Lead': 0.6,
    
    # Data
    'Data Scientist': 0.6,
    'Data Analyst': 0.8,
    'Data Engineer': 0.7,
    'Machine Learning Engineer': 0.5,
    'AI Researcher': 0.4,
    'Business Intelligence Analyst': 0.8,
    'Business Analyst': 0.85,
    'Data Entry Clerk': 0.95,
    'Data Entry Specialist': 0.95,
    
    # Design
    'Graphic Designer': 0.85,
    'UI Designer': 0.8,
    'UX Designer': 0.75,
    'UI/UX Designer': 0.8,
    'Product Designer': 0.75,
    'Web Designer': 0.85,
    'Visual Designer': 0.85,
    'Illustrator': 0.75,
    'Art Director': 0.65,
    'Creative Director': 0.6,
    
    # Management
    'Project Manager': 0.5,
    'Product Manager': 0.55,
    'Program Manager': 0.6,
    'Operations Manager': 0.7,
    'Office Manager': 0.85,
    'CEO': 0.7,
    'Chief Executive Officer': 0.7,
    'CFO': 0.6,
    'Chief Financial Officer': 0.6,
    'COO': 0.5,
    'Chief Operating Officer': 0.5,
    'Director': 0.5,
    'Vice President': 0.5,
    'Manager': 0.7,
    'Team Lead': 0.6,
    'Supervisor': 0.8,
    
    # Marketing
    'Marketing Manager': 0.6,
    'Marketing Specialist': 0.8,
    'Digital Marketing Specialist': 0.8,
    'SEO Specialist': 0.85,
    'Social Media Manager': 0.8,
    'Content Writer': 0.9,
    'Content Creator': 0.85,
    'Copywriter': 0.9,
    'Content Strategist': 0.75,
    'Brand Manager': 0.7,
    'Public Relations Specialist': 0.75,
    'Communications Specialist': 0.75,
    
    # Sales
    'Sales Representative': 0.85,
    'Sales Associate': 0.9,
    'Account Executive': 0.75,
    'Account Manager': 0.7,
    'Business Development Manager': 0.7,
    'Sales Manager': 0.7,
    'Customer Success Manager': 0.75,
    
    # HR
    'HR Manager': 0.7,
    'Human Resources Manager': 0.7,
    'HR Specialist': 0.85,
    'Human Resources Specialist': 0.85,
    'Recruiter': 0.85,
    'Talent Acquisition Specialist': 0.85,
    'HR Coordinator': 0.9,
    'Human Resources Coordinator': 0.9,
    
    # Finance
    'Accountant': 0.9,
    'Financial Analyst': 0.75,
    'Financial Advisor': 0.85,
    'Bookkeeper': 0.95,
    'Auditor': 0.85,
    'Tax Preparer': 0.95,
    'Investment Banker': 0.75,
    'Investment Analyst': 0.75,
    'Loan Officer': 0.9,
    'Insurance Agent': 0.9,
    
    # Healthcare
    'Doctor': 0.45,
    'Physician': 0.45,
    'Surgeon': 0.35,
    'Nurse': 0.55,
    'Registered Nurse': 0.55,
    'Nurse Practitioner': 0.45,
    'Medical Assistant': 0.75,
    'Pharmacist': 0.75,
    'Pharmacy Technician': 0.9,
    'Physical Therapist': 0.55,
    'Occupational Therapist': 0.55,
    'Dentist': 0.45,
    'Dental Hygienist': 0.65,
    'Veterinarian': 0.45,
    'Vet Tech': 0.75,
    
    # Education
    'Teacher': 0.65,
    'Professor': 0.55,
    'Tutor': 0.75,
    'School Administrator': 0.65,
    'Principal': 0.55,
    'Librarian': 0.85,
    'Research Assistant': 0.75,
    'Researcher': 0.55,
    
    # Legal
    'Lawyer': 0.75,
    'Attorney': 0.75,
    'Paralegal': 0.9,
    'Legal Assistant': 0.9,
    'Judge': 0.45,
    'Legal Counsel': 0.75,
    
    # Service Industry
    'Chef': 0.55,
    'Cook': 0.85,
    'Waiter': 0.95,
    'Waitress': 0.95,
    'Server': 0.95,
    'Bartender': 0.9,
    'Barista': 0.9,
    'Host': 0.95,
    'Hostess': 0.95,
    'Housekeeper': 0.95,
    'Janitor': 0.9,
    'Custodian': 0.9,
    'Cleaner': 0.95,
    'Security Guard': 0.9,
    'Receptionist': 0.95,
    'Customer Service Representative': 0.95,
    'Customer Support': 0.9,
    'Call Center Agent': 0.98,
    
    # Transportation
    'Truck Driver': 0.95,
    'Delivery Driver': 0.95,
    'Uber Driver': 0.98,
    'Lyft Driver': 0.98,
    'Taxi Driver': 0.98,
    'Bus Driver': 0.95,
    'Pilot': 0.75,
    'Flight Attendant': 0.85,
    
    # Retail
    'Retail Worker': 0.95,
    'Retail Associate': 0.95,
    'Cashier': 0.98,
    'Store Manager': 0.85,
    'Store Associate': 0.95,
    'Sales Clerk': 0.95,
    
    # Creative
    'Photographer': 0.75,
    'Videographer': 0.65,
    'Video Editor': 0.75,
    'Film Editor': 0.75,
    'Actor': 0.55,
    'Actress': 0.55,
    'Musician': 0.55,
    'Writer': 0.75,
    'Journalist': 0.85,
    'Reporter': 0.85,
    'Editor': 0.75,
    
    # Trades
    'Electrician': 0.65,
    'Plumber': 0.65,
    'Carpenter': 0.75,
    'Construction Worker': 0.85,
    'Mechanic': 0.75,
    'HVAC Technician': 0.75,
    'Welder': 0.85,
    'Machinist': 0.9,
    'Factory Worker': 0.95,
    'Assembly Line Worker': 0.98,
    
    # Miscellaneous
    'Consultant': 0.65,
    'Freelancer': 0.75,
    'Contractor': 0.85,
    'Analyst': 0.75,
    'Specialist': 0.85,
    'Coordinator': 0.9,
    'Assistant': 0.95,
    'Intern': 0.9,
    'Student': 0.85
}

# Add startup-specific job titles to the job_risks dictionary
startup_jobs = {
    # Startup Leadership
    'Founder': 0.7,
    'Co-Founder': 0.7,
    'Startup CEO': 0.7,
    'Startup CTO': 0.5,
    'Technical Co-Founder': 0.5,
    'Non-Technical Co-Founder': 0.6,
    'Founding Engineer': 0.6,
    'Chief Product Officer': 0.55,
    'Chief Revenue Officer': 0.6,
    'Chief Marketing Officer': 0.65,
    'Chief Growth Officer': 0.6,
    'Chief of Staff': 0.7,
    'VP of Product': 0.6,
    'Head of Product': 0.6,
    'VP of Engineering': 0.55,
    'Head of Engineering': 0.55,
    'VP of Design': 0.7,
    'Head of Design': 0.7,
    'VP of Sales': 0.6,
    'Head of Sales': 0.6,
    'VP of Marketing': 0.65,
    'Head of Marketing': 0.65,
    'VP of Operations': 0.7,
    'Head of Operations': 0.7,
    'VP of People': 0.8,
    'Head of People': 0.8,
    'VP of Customer Success': 0.7,
    'Head of Customer Success': 0.7,
    'VP of Business Development': 0.6,
    'Head of Business Development': 0.6,
    
    # Startup-specific roles
    'Growth Hacker': 0.8,
    'Growth Marketer': 0.8,
    'Product Manager': 0.6,
    'Product Owner': 0.6,
    'Scrum Master': 0.85,
    'DevOps Engineer': 0.7,
    'Full Stack Developer': 0.7,
    'Frontend Engineer': 0.75,
    'Backend Engineer': 0.65,
    'Mobile Developer': 0.7,
    'UI/UX Designer': 0.8,
    'Product Designer': 0.75,
    'Customer Success Manager': 0.8,
    'Community Manager': 0.85,
    'Content Marketer': 0.85,
    'SEO Specialist': 0.9,
    'SEM Specialist': 0.9,
    'Paid Acquisition Manager': 0.85,
    'Venture Capital Associate': 0.75,
    'Venture Capital Analyst': 0.85,
    'Angel Investor': 0.5,
    'Startup Advisor': 0.6,
    'Startup Mentor': 0.5,
    'Startup Coach': 0.6,
    'Pitch Deck Consultant': 0.85,
    'Startup Recruiter': 0.85,
    'Technical Recruiter': 0.85,
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
    Returns risk as a percentage with some randomness.
    """
    # Clean the job title for better matching
    cleaned_job_title = job_title.lower().strip()
    
    # Base risk value
    base_risk = None
    
    # Try exact match first
    for key in job_risks:
        if key.lower() == cleaned_job_title:
            base_risk = job_risks[key] * 100
            break
    
    # If no exact match, try fuzzy matching
    if base_risk is None:
        best_match = process.extractOne(cleaned_job_title, job_risks.keys())
        
        # Lower threshold to 70% for more matches
        if best_match and best_match[1] > 70:
            base_risk = job_risks[best_match[0]] * 100
    
    # If still no match, try matching on parts of the job title
    if base_risk is None:
        words = cleaned_job_title.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 3:  # Only consider meaningful words
                    word_match = process.extractOne(word, job_risks.keys())
                    if word_match and word_match[1] > 80:
                        base_risk = job_risks[word_match[0]] * 100
                        break
    
    # Default risk if no match found (medium risk)
    if base_risk is None:
        print(f"No match found for job title: {job_title}")
        base_risk = 50.0
    
    # Add randomness to the risk score
    # For tech audience, we want more variability
    random_factor = random.uniform(-10, 10)  # Random value between -10 and 10
    
    # Special case for founders and CEOs - ensure they get high risk
    if any(keyword in cleaned_job_title for keyword in ['founder', 'co-founder', 'ceo', 'chief executive']):
        # For founders and CEOs, ensure risk is at least 65% and add some randomness
        base_risk = max(base_risk, 65.0)
        random_factor = random.uniform(0, 10)  # Only positive randomness for founders/CEOs
    
    # Apply randomness
    final_risk = base_risk + random_factor
    
    # Ensure risk stays within 5-95% range (we don't want 0% or 100% for dramatic effect)
    final_risk = max(5.0, min(95.0, final_risk))
    
    return final_risk

# Function to generate a humorous roast
def generate_roast(profile_info, risk, has_profile_pic=False):
    """
    Uses OpenAI API to generate a funny roast based on profile and risk.
    """
    # Determine the specific executive type for more targeted roasts
    job_title_lower = profile_info['job_title'].lower()
    company_lower = profile_info['company'].lower()
    
    # More specific executive type detection
    is_founder = any(keyword in job_title_lower for keyword in ['founder', 'co-founder', 'founding'])
    is_ceo = any(keyword in job_title_lower for keyword in ['ceo', 'chief executive', 'chief exec'])
    is_cto = any(keyword in job_title_lower for keyword in ['cto', 'chief technology', 'chief tech'])
    is_other_exec = any(keyword in job_title_lower for keyword in ['chief', 'head of', 'vp', 'director', 'lead'])
    
    # Determine if this is likely a startup
    is_startup = 'startup' in job_title_lower or 'startup' in company_lower or risk > 40
    
    # Determine executive type for roast customization
    exec_type = "generic"
    if is_founder:
        exec_type = "founder"
    elif is_ceo:
        exec_type = "ceo"
    elif is_cto:
        exec_type = "cto"
    elif is_other_exec:
        exec_type = "executive"
    
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
    
    # Add executive-specific context
    exec_context = ""
    if exec_type == "founder":
        exec_context = "This person is a founder. Roast them about typical founder traits like overconfidence, pivoting too much, unrealistic expectations, living on ramen while claiming to be 'crushing it', pitching to VCs who don't understand their product, or having a 'revolutionary' idea that's actually been done 100 times before."
    elif exec_type == "ceo":
        exec_context = "This person is a CEO. Roast them about typical CEO traits like taking credit for others' work, making meaningless corporate announcements, having an inflated salary compared to employees, spending too much time on CNBC instead of running the company, or making decisions based on what they read in airport business books."
    elif exec_type == "cto":
        exec_context = "This person is a CTO. Roast them about typical CTO traits like being out of touch with actual coding, choosing trendy tech stacks that nobody can maintain, claiming to be 'technical' despite not having written code in years, or creating architecture diagrams that nobody understands."
    elif exec_type == "executive":
        exec_context = "This person is an executive. Roast them about typical executive traits like having meetings about meetings, using buzzwords nobody understands, making strategic pivots that are actually just panic moves, or having an impressive title for a company of 5 people."
    
    if is_startup:
        prompt = (
            f"You are a comedy writer tasked with roasting a {exec_type} based on their resume.\n"
            "Your roast should be funny, creative, and have personality. Use colorful language, clever analogies, and humorous observations.\n"
            "Keep it light-hearted and non-offensive, but make it specifically relevant to startup culture and the tech industry.\n"
            f"{exec_context}\n"
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
            "Write a short, funny roast (2-3 sentences) focusing on their job's automation risk and their position in the matrix quadrant.\n"
            "IMPORTANT: Ensure your response uses proper sentence structure and punctuation. Make it funny without being corny.\n"
            "For reference, here's a good example of the tone and style: 'Rameel's smile looks like he just discovered the magic of flash photography for the first time. His LinkedIn skills list is probably longer than his Tinder matches. That shirt has more stars than his career prospects. Forget shooting for the stars, buddy, aim for a reasonable payday instead!'"
        )
    else:
        prompt = (
            "You are a comedy writer tasked with roasting someone based on their resume.\n"
            "Your roast should be funny, creative, and have personality. Use colorful language, clever analogies, and humorous observations.\n"
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
            "Write a short, funny roast (2-3 sentences) focusing on their job's automation risk and their position in the matrix quadrant.\n"
            "IMPORTANT: Ensure your response uses proper sentence structure and punctuation. Make it funny without being corny.\n"
            "For reference, here's a good example of the tone and style: 'Rameel's smile looks like he just discovered the magic of flash photography for the first time. His LinkedIn skills list is probably longer than his Tinder matches. That shirt has more stars than his career prospects. Forget shooting for the stars, buddy, aim for a reasonable payday instead!'"
        )
    
    try:
        # Use chat completions API instead of completions for better reliability
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a comedy writer who specializes in clever, funny roasts with personality. You use colorful language and creative analogies without being corny."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.8,
            presence_penalty=0.6,  # Encourage more unique responses
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
                <a class="share-button" href="https://x.com/ramshe1000/status/1900170017733214506" target="_blank">Share on X</a>
                <a class="share-button" href="https://www.linkedin.com/feed/update/urn:li:activity:7305935971458457600/" target="_blank">Share on LinkedIn</a>
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