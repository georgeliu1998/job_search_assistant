"""
Fit assessment prompt for structured outputs.

Guides the LLM to judge whether a job posting is a good fit for the user's
target role and skills, based on the actual focus areas and responsibilities of
the role rather than the title alone.
"""

from langchain_core.prompts import PromptTemplate

FIT_ASSESSMENT_RAW_TEMPLATE = """
You are assessing whether a job posting is a good fit for a candidate.

Compare the candidate's target role and key skills against the job's actual
focus areas, responsibilities, and required skills. Do not rely on the job
title alone -- a similar title with a different focus may still be a poor fit
(for example, an "AI Engineer" who builds LLM/RAG systems is a poor fit for a
"Data Scientist" role centered on A/B testing and recommendation engines).

Return:
- verdict: "good_fit" if the candidate's profile aligns well with the role's
  focus and the candidate would likely be a strong applicant; otherwise
  "poor_fit".
- reasoning: one or two sentences explaining the verdict.

Candidate's target role:
{target_role_description}

Candidate's key skills:
{key_skills}

Job posting:
{job_text}
"""

FIT_ASSESSMENT_PROMPT = PromptTemplate.from_template(FIT_ASSESSMENT_RAW_TEMPLATE)
