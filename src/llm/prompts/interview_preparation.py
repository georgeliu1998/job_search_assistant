"""
Interview preparation prompt templates.
"""

from langchain_core.prompts import PromptTemplate

INTERVIEW_PREP_PROMPT_TEMPLATE = """
You are an expert interview coach helping a candidate prepare for a job interview.
Please provide a comprehensive interview preparation guide based on the information provided below.

**INTERVIEW DETAILS:**
- Position: {job_description}
- Interview Type: {interview_type}
- Interviewer: {interviewer_info}
- Company Website: {company_website}

**CANDIDATE'S RESUME:**
{resume_text}

**ADDITIONAL CONTEXT:**
{additional_context}

Please provide a detailed interview preparation guide that includes:

## 1. Interview Overview & Strategy
- What to expect for this type of interview
- Key success factors and approach
- Specific preparation timeline recommendations

## 2. Likely Interview Questions & Suggested Answers
Generate 8-12 questions specific to this role and interview type, with personalized suggested answers based on the candidate's background. Include:
- **Behavioral Questions**: Focus on past experiences and situational responses
- **Technical Questions**: Relevant to the role requirements (if applicable)
- **Company/Role-Specific Questions**: Based on the job description and company context
- **Motivation Questions**: Why this role, why this company

For each question, provide:
- The question
- A suggested answer framework
- Key points to emphasize from the candidate's background

## 3. Company & Role Insights
- Analysis of the company and position based on available information
- Key talking points to demonstrate fit and interest
- Company culture insights and alignment opportunities
- Recent company news or developments (if website provided)

## 4. Questions to Ask the Interviewer
Provide 5-7 thoughtful questions tailored to:
- The interview type and interviewer's role
- The specific position and company
- Showing genuine interest and preparation

## 5. Final Preparation Tips
- Specific advice for this interview situation
- Key reminders and confidence boosters
- Last-minute preparation checklist
- How to handle common challenges for this interview type

## 6. Interview Day Strategy
- What to bring and how to prepare
- How to make a strong first impression
- Key points to remember during the interview
- How to close the interview effectively

Please format your response clearly with headers, bullet points, and specific examples. Make the advice actionable and personalized to the candidate's background and the specific opportunity.

Remember to:
- Tailor all advice to the specific interview type
- Reference specific details from the candidate's resume
- Provide concrete examples and talking points
- Include confidence-building elements
- Make the guidance practical and actionable
"""

# Create the prompt template
INTERVIEW_PREPARATION_PROMPT = PromptTemplate.from_template(
    INTERVIEW_PREP_PROMPT_TEMPLATE
)
