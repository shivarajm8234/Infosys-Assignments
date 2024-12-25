import json
import os
from datetime import datetime
from typing import List, Dict
import PyPDF2
import requests
from dataclasses import dataclass
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from groq import Groq
import asyncio
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it with your Groq API key.")
groq_client = Groq(api_key=GROQ_API_KEY)

@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    description: str
    required_skills: List[str]
    salary_range: str
    posting_date: str

class JobSearchUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Search Assistant (Powered by Groq)")
        self.root.geometry("1000x800")
        self.assistant = JobSearchAssistant()
        
        # Configure style
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """Setup custom styles for widgets"""
        style = ttk.Style()
        
        # Configure colors
        self.bg_color = "#f0f2f5"
        self.accent_color = "#1a73e8"
        self.text_color = "#202124"
        self.secondary_color = "#5f6368"
        
        # Configure base style
        style.configure(".", 
                      font=("Helvetica", 10),
                      background=self.bg_color,
                      foreground=self.text_color)
        
        # Configure labels
        style.configure("Title.TLabel",
                      font=("Helvetica", 24, "bold"),
                      padding=10,
                      foreground=self.accent_color)
        
        style.configure("Subtitle.TLabel",
                      font=("Helvetica", 12),
                      padding=5,
                      foreground=self.secondary_color)
        
        style.configure("Header.TLabel",
                      font=("Helvetica", 14, "bold"),
                      padding=5,
                      foreground=self.text_color)
        
        # Configure frames
        style.configure("Card.TFrame",
                      padding=15,
                      relief="solid",
                      borderwidth=1,
                      background="white")
        
        style.configure("MainFrame.TFrame",
                      padding=20,
                      background=self.bg_color)
        
        # Configure buttons
        style.configure("Primary.TButton",
                      font=("Helvetica", 10, "bold"),
                      padding=10,
                      background=self.accent_color,
                      foreground="white")
        
        style.configure("Secondary.TButton",
                      font=("Helvetica", 10),
                      padding=8)
        
        # Configure labelframes
        style.configure("Card.TLabelframe",
                      padding=15,
                      relief="solid",
                      borderwidth=1,
                      background="white")
        
        style.configure("Card.TLabelframe.Label",
                      font=("Helvetica", 12, "bold"),
                      foreground=self.accent_color,
                      background="white")
        
    def create_widgets(self):
        """Create and arrange UI widgets"""
        # Configure root
        self.root.configure(bg=self.bg_color)
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, style="MainFrame.TFrame")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_frame = ttk.Frame(main_frame, style="MainFrame.TFrame")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="Job Search Assistant", style="Title.TLabel")
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ttk.Label(title_frame, text="Powered by Groq AI", style="Subtitle.TLabel")
        subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Left panel (Input fields)
        left_panel = ttk.Frame(main_frame, style="MainFrame.TFrame")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Resume section
        resume_frame = ttk.LabelFrame(left_panel, text="Resume Upload", style="Card.TLabelframe")
        resume_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        resume_frame.grid_columnconfigure(0, weight=1)
        
        self.resume_path_var = tk.StringVar()
        browse_button = ttk.Button(resume_frame, text="📄 Upload Resume (PDF)", command=self.browse_resume, style="Primary.TButton")
        browse_button.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.resume_label = ttk.Label(resume_frame, text="No resume selected", wraplength=300)
        self.resume_label.grid(row=1, column=0, sticky="w")
        
        # Profile Display
        profile_frame = ttk.LabelFrame(left_panel, text="Your Profile", style="Card.TLabelframe")
        profile_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        profile_frame.grid_columnconfigure(0, weight=1)
        
        self.profile_text = tk.Text(profile_frame, wrap=tk.WORD, height=8, font=("Helvetica", 10))
        self.profile_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.profile_text.configure(state="disabled")
        
        # Search preferences section
        pref_frame = ttk.LabelFrame(left_panel, text="Search Preferences", style="Card.TLabelframe")
        pref_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        pref_frame.grid_columnconfigure(1, weight=1)
        
        # Job search
        ttk.Label(pref_frame, text="🔍 Job Title:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.job_search_var = tk.StringVar()
        ttk.Entry(pref_frame, textvariable=self.job_search_var, width=30).grid(row=0, column=1, sticky="ew", padx=5)
        
        # Locations
        ttk.Label(pref_frame, text="📍 Locations:", style="Header.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.locations_var = tk.StringVar()
        ttk.Entry(pref_frame, textvariable=self.locations_var, width=30).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Label(pref_frame, text="Separate multiple locations with commas", style="Subtitle.TLabel").grid(row=2, column=1, sticky="w", padx=5)
        
        # Minimum salary
        ttk.Label(pref_frame, text="💰 Min Salary:", style="Header.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        self.min_salary_var = tk.StringVar(value="0")
        ttk.Entry(pref_frame, textvariable=self.min_salary_var, width=30).grid(row=3, column=1, sticky="ew", padx=5)
        
        # Remote preference
        self.remote_var = tk.BooleanVar()
        ttk.Checkbutton(pref_frame, text="🏠 Remote Only", variable=self.remote_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Search button
        search_button = ttk.Button(left_panel, text="🔍 Search Jobs", command=self.search_jobs, style="Primary.TButton")
        search_button.grid(row=3, column=0, sticky="ew", pady=10)
        
        # Right panel (Results)
        right_panel = ttk.Frame(main_frame, style="Card.TFrame")
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)
        
        # Results header
        ttk.Label(right_panel, text="Job Recommendations", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Results text area with scrollbar
        results_frame = ttk.Frame(right_panel, style="Card.TFrame")
        results_frame.grid(row=1, column=0, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, width=50, height=30)
        self.results_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.results_text.configure(font=("Helvetica", 10))
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
    def update_profile_display(self):
        """Update the profile display with current user profile information"""
        self.profile_text.configure(state="normal")
        self.profile_text.delete(1.0, tk.END)
        
        if not self.assistant.user_profile:
            self.profile_text.insert(tk.END, "No profile information available.\nPlease upload a resume to see your profile details.")
        else:
            self.profile_text.insert(tk.END, "📊 Experience Level: " + self.assistant.user_profile["experience_level"] + "\n\n")
            
            self.profile_text.insert(tk.END, "🎯 Skills:\n")
            for skill in self.assistant.user_profile["skills"]:
                self.profile_text.insert(tk.END, f"  • {skill}\n")
            
            if self.assistant.user_profile["achievements"]:
                self.profile_text.insert(tk.END, "\n🏆 Key Achievements:\n")
                for achievement in self.assistant.user_profile["achievements"]:
                    self.profile_text.insert(tk.END, f"  • {achievement}\n")
        
        self.profile_text.configure(state="disabled")
        
    def browse_resume(self):
        """Browse for resume file"""
        file_path = filedialog.askopenfilename(
            title="Select Resume",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            try:
                self.resume_path_var.set(file_path)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Analyzing resume... Please wait.\n")
                self.root.update()
                
                # Initialize preferences
                preferences = {
                    "preferred_locations": [],
                    "minimum_salary": 0,
                    "remote_only": False
                }
                
                # Update assistant with resume and preferences
                resume_path = self.resume_path_var.get()
                if resume_path:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.assistant.update_user_profile(resume_path, preferences))
                    loop.close()
                    
                    # Show the extracted information
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, "Resume Analysis Results:\n\n")
                    self.results_text.insert(tk.END, f"Experience Level: {self.assistant.user_profile['experience_level']}\n\n")
                    
                    self.results_text.insert(tk.END, "Skills:\n")
                    for skill in self.assistant.user_profile['skills']:
                        self.results_text.insert(tk.END, f"- {skill}\n")
                    self.results_text.insert(tk.END, "\n")
                    
                    self.results_text.insert(tk.END, "Key Achievements:\n")
                    for achievement in self.assistant.user_profile['achievements']:
                        self.results_text.insert(tk.END, f"- {achievement}\n")
                    
                else:
                    self.assistant.user_profile = {
                        "skills": [],
                        "experience_level": "Entry Level",
                        "achievements": [],
                        "preferred_locations": [],
                        "minimum_salary": 0,
                        "remote_only": False
                    }
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, "No resume selected. Using default profile.\n")
                
                self.update_profile_display()
                
            except Exception as e:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Error processing resume: {str(e)}\n")
                
    def search_jobs(self):
        try:
            # Get preferences
            preferences = {
                "job_search": self.job_search_var.get().strip(),
                "preferred_locations": [loc.strip() for loc in self.locations_var.get().split(",") if loc.strip()],
                "minimum_salary": int(self.min_salary_var.get()) if self.min_salary_var.get().strip() else 0,
                "remote_only": self.remote_var.get()
            }
            
            if not preferences["job_search"]:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Please enter a job title to search for.\n")
                return
                
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Searching for jobs... Please wait.\n")
            self.root.update()
            
            # Update the user profile with current preferences
            if not self.assistant.user_profile:
                self.assistant.user_profile = {
                    "skills": [],
                    "experience_level": "Entry Level",
                    "achievements": [],
                    "preferred_locations": preferences["preferred_locations"],
                    "minimum_salary": preferences["minimum_salary"],
                    "remote_only": preferences["remote_only"]
                }
                self.update_profile_display()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            recommendations = loop.run_until_complete(self.assistant.get_job_recommendations_groq(preferences["job_search"]))
            loop.close()
            
            if not recommendations:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "No job postings found. Please try a different search term.\n")
                return
                
            self.display_recommendations(recommendations)
            
        except ValueError as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Invalid input: {str(e)}\n")
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error searching for jobs: {str(e)}\n")
            
    def display_recommendations(self, recommendations):
        """Display job recommendations with improved formatting"""
        self.results_text.delete(1.0, tk.END)
        
        if not recommendations:
            self.results_text.insert(tk.END, "No matching jobs found. Try adjusting your search criteria.\n")
            return
            
        for i, rec in enumerate(recommendations, 1):
            job = rec["job"]
            match_score = rec["match_score"]
            
            # Add job header with match score
            self.results_text.insert(tk.END, f"\n{'='*50}\n")
            self.results_text.insert(tk.END, f"Job #{i} - Match Score: {match_score:.1f}%\n")
            self.results_text.insert(tk.END, f"{'='*50}\n\n")
            
            # Add job details
            self.results_text.insert(tk.END, f"🏢 Company: {job.company}\n")
            self.results_text.insert(tk.END, f"📋 Title: {job.title}\n")
            self.results_text.insert(tk.END, f"📍 Location: {job.location}\n")
            self.results_text.insert(tk.END, f"💰 Salary Range: {job.salary_range}\n")
            self.results_text.insert(tk.END, f"📅 Posted: {job.posting_date}\n\n")
            
            # Add skills section
            self.results_text.insert(tk.END, "Required Skills:\n")
            for skill in job.required_skills:
                self.results_text.insert(tk.END, f"  • {skill}\n")
            self.results_text.insert(tk.END, "\n")
            
            # Add description
            self.results_text.insert(tk.END, "Description:\n")
            self.results_text.insert(tk.END, f"{job.description}\n")
            
            # Add separator between jobs
            if i < len(recommendations):
                self.results_text.insert(tk.END, f"\n{'-'*50}\n")

class JobSearchAssistant:
    def __init__(self):
        self.job_database: List[JobPosting] = []
        self.user_profile = {}
        self.vectorizer = TfidfVectorizer(stop_words='english')

    async def fetch_jobs_from_groq(self, job_search: str) -> List[JobPosting]:
        """Fetch job postings using Groq API"""
        try:
            prompt = f"""
            Generate 5 detailed job postings for the position: {job_search}
            
            Please format your response EXACTLY as a JSON array of job objects with the following structure:
            [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "City, State or Remote",
                    "description": "Detailed job description...",
                    "required_skills": ["skill1", "skill2", "skill3"],
                    "salary_range": "$X0,000 - $Y0,000",
                    "posting_date": "YYYY-MM-DD"
                }},
                // ... more job objects
            ]

            Requirements:
            1. Each job must have ALL the fields mentioned above
            2. required_skills must be a list of strings
            3. salary_range should be in the format "$X0,000 - $Y0,000"
            4. posting_date should be within the last week
            5. Include some remote positions
            6. Make descriptions detailed but concise
            
            Return ONLY the JSON array, no additional text.
            """
            
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, lambda: groq_client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=4000
            ))
            
            response_text = completion.choices[0].message.content
            # Clean the response text to ensure it's valid JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                jobs_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}")
                print(f"Raw response: {response_text}")
                raise Exception("Failed to parse Groq API response")
            
            if not isinstance(jobs_data, list):
                raise Exception("API response is not a list of jobs")
            
            job_postings = []
            for job in jobs_data:
                # Ensure all required fields are present with default values if missing
                processed_job = {
                    "title": job.get("title", "Untitled Position"),
                    "company": job.get("company", "Unknown Company"),
                    "location": job.get("location", "Location Not Specified"),
                    "description": job.get("description", "No description available"),
                    "required_skills": job.get("required_skills", []),
                    "salary_range": job.get("salary_range", "Salary Not Specified"),
                    "posting_date": job.get("posting_date", datetime.now().strftime("%Y-%m-%d"))
                }
                
                # Ensure required_skills is a list
                if not isinstance(processed_job["required_skills"], list):
                    if isinstance(processed_job["required_skills"], str):
                        processed_job["required_skills"] = [skill.strip() for skill in processed_job["required_skills"].split(",")]
                    else:
                        processed_job["required_skills"] = []
                
                posting = JobPosting(
                    title=processed_job["title"],
                    company=processed_job["company"],
                    location=processed_job["location"],
                    description=processed_job["description"],
                    required_skills=processed_job["required_skills"],
                    salary_range=processed_job["salary_range"],
                    posting_date=processed_job["posting_date"]
                )
                job_postings.append(posting)
            
            return job_postings
            
        except Exception as e:
            print(f"Full error in fetch_jobs_from_groq: {str(e)}")
            # Return an empty list instead of raising an exception
            return []

    def extract_text_from_resume(self, resume_path: str) -> str:
        """Extract text content from a PDF resume"""
        text = ""
        try:
            with open(resume_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            raise Exception(f"Error extracting text from resume: {str(e)}")
        return text

    async def analyze_resume_with_groq(self, resume_text: str) -> Dict:
        """Analyze resume using Groq API"""
        try:
            prompt = f"""
            Analyze the following resume and extract key information in JSON format.
            
            Please format your response EXACTLY as follows:
            {{
                "skills": {{
                    "technical": ["skill1", "skill2", ...],
                    "soft": ["skill1", "skill2", ...]
                }},
                "experience_level": "Entry Level|Mid Level|Senior Level",
                "achievements": [
                    "achievement1",
                    "achievement2",
                    ...
                ]
            }}

            Resume text:
            {resume_text}
            
            Remember to return ONLY the JSON object, no additional text.
            """
            
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, lambda: groq_client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=2000
            ))
            
            response_text = completion.choices[0].message.content
            # Clean the response text to ensure it's valid JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}")
                print(f"Raw response: {response_text}")
                raise Exception("Failed to parse Groq API response")
            
            # Ensure all required fields are present
            if "skills" not in analysis:
                analysis["skills"] = {"technical": [], "soft": []}
            if "experience_level" not in analysis:
                analysis["experience_level"] = "Entry Level"
            if "achievements" not in analysis:
                analysis["achievements"] = []
                
            # Combine technical and soft skills
            all_skills = []
            if isinstance(analysis["skills"], dict):
                all_skills.extend(analysis["skills"].get("technical", []))
                all_skills.extend(analysis["skills"].get("soft", []))
            elif isinstance(analysis["skills"], list):
                all_skills = analysis["skills"]
            
            return {
                "skills": all_skills,
                "experience_level": analysis["experience_level"],
                "achievements": analysis["achievements"]
            }
            
        except Exception as e:
            print(f"Full error in analyze_resume_with_groq: {str(e)}")
            return {
                "skills": [],
                "experience_level": "Entry Level",
                "achievements": []
            }

    async def update_user_profile(self, resume_path: str, preferences: Dict):
        """Update user profile with resume analysis and preferences"""
        resume_text = self.extract_text_from_resume(resume_path)
        resume_analysis = await self.analyze_resume_with_groq(resume_text)
        
        self.user_profile = {
            "skills": resume_analysis["skills"],
            "experience_level": resume_analysis["experience_level"],
            "achievements": resume_analysis.get("achievements", []),
            "preferred_locations": preferences.get("preferred_locations", []),
            "minimum_salary": preferences.get("minimum_salary", 0),
            "remote_only": preferences.get("remote_only", False)
        }

    def calculate_job_match_score(self, job: JobPosting) -> float:
        """Calculate match score between user profile and job posting"""
        if not self.user_profile:
            return 0.0

        score = 0.0
        max_score = 100.0

        # Skills match (40% of total score)
        user_skills = set(skill.lower() for skill in self.user_profile["skills"])
        job_skills = set(skill.lower() for skill in job.required_skills)
        if user_skills and job_skills:
            skills_match = len(user_skills.intersection(job_skills)) / len(job_skills)
            score += skills_match * 40

        # Location match (30% of total score)
        if self.user_profile["remote_only"] and "remote" in job.location.lower():
            score += 30
        elif any(loc.lower() in job.location.lower() for loc in self.user_profile["preferred_locations"]):
            score += 30

        # Salary match (30% of total score)
        try:
            salary_text = re.findall(r'\d+', job.salary_range.replace(',', ''))
            if salary_text:
                min_salary = int(salary_text[0])
                if min_salary >= self.user_profile["minimum_salary"]:
                    score += 30
        except:
            pass

        return min(score, max_score)

    async def get_job_recommendations_groq(self, job_search: str) -> List[Dict]:
        """Get personalized job recommendations using Groq"""
        try:
            # Fetch jobs using Groq
            job_postings = await self.fetch_jobs_from_groq(job_search)
            
            # Calculate match scores
            recommendations = []
            for job in job_postings:
                match_score = self.calculate_job_match_score(job)
                recommendations.append({
                    "job": job,
                    "match_score": match_score
                })

            # Sort by match score
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            return recommendations
            
        except Exception as e:
            raise Exception(f"Error getting job recommendations: {str(e)}")

def main():
    root = tk.Tk()
    app = JobSearchUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()