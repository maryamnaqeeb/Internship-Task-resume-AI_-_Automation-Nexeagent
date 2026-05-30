import streamlit as st
from pypdf import PdfReader
from google import genai
from google.genai import types
import json

# Page Configuration
st.set_page_config(page_title="AI Resume Screener", page_icon="📄", layout="wide")

# API Key input setup
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

st.title("📄 Advanced AI Resume Screener")
st.markdown("Upload a resume and paste the job description to get instant matching insights.")

# PDF text extractor function
def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# AI Analysis function using Google GenAI SDK
def analyze_resume(resume_text, job_desc, api_key):
    # Initialize the client with the provided API key
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and HR Manager. 
    Analyze the following Resume against the Job Description.
    
    Resume Text:
    {resume_text}
    
    Job Description:
    {job_desc}
    
    Provide the response strictly in JSON format with the following keys. Do not include markdown code fences or extra text, just the raw JSON object:
    {{
        "match_percentage": int (0 to 100),
        "matched_skills": ["list", "of", "skills"],
        "missing_skills": ["list", "of", "skills", "required", "but", "missing"],
        "summary": "2-3 sentences feedback on candidate alignment"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            # Force JSON output structure
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"AI Generation Error: {e}")
        return None

# UI Layout: Two columns for input
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Position Details")
    job_desc = st.text_area("Paste Job Description (JD) here:", height=300)

with col2:
    st.subheader("2. Candidate Information")
    uploaded_file = st.file_uploader("Upload Resume (PDF format only)", type=["pdf"])

st.markdown("---")

# Action Button
if st.button("Run AI Screener Analysis", type="primary"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar first.")
    elif not job_desc:
        st.warning("Please paste a Job Description.")
    elif not uploaded_file:
        st.warning("Please upload a Resume PDF.")
    else:
        with st.spinner("Extracting text and consulting Gemini AI..."):
            # Step 1: Extract Text
            resume_text = extract_text_from_pdf(uploaded_file)
            
            if resume_text:
                # Step 2 & 3: AI Processing
                result = analyze_resume(resume_text, job_desc, api_key)
                
                if result:
                    st.success("Analysis Completed Successfully!")
                    
                    # Display Results Metrics
                    score = result.get("match_percentage", 0)
                    
                    # Color coding logic based on score
                    if score >= 75:
                        st.balloons()
                        st.metric(label="Match Score (Strong Fit)", value=f"{score}%")
                    elif score >= 50:
                        st.metric(label="Match Score (Moderate Fit)", value=f"{score}%")
                    else:
                        st.metric(label="Match Score (Low Fit)", value=f"{score}%")
                        
                    st.subheader("Executive Summary")
                    st.write(result.get("summary", "No summary provided."))
                    
                    # Columns for Skills breakdown
                    scol1, scol2 = st.columns(2)
                    with scol1:
                        st.subheader("✅ Matched Skills")
                        skills = result.get("matched_skills", [])
                        if skills:
                            for skill in skills:
                                st.markdown(f"- {skill}")
                        else:
                            st.write("No matching skills identified.")
                            
                    with scol2:
                        st.subheader("❌ Missing / Gap Skills")
                        missing = result.get("missing_skills", [])
                        if missing:
                            for skill in missing:
                                st.markdown(f"- {skill}")
                        else:
                            st.write("No major gaps found for this role!")