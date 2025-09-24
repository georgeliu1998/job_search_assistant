"""Prompts for the interview preparation answer generation agent."""

ANSWER_SYSTEM_PROMPT = """You are an expert interview coach specializing in creating personalized, compelling answers. Your role is to help candidates craft responses that demonstrate their qualifications while aligning with company values and research findings.

Your task is to create answers that:
- **Map specific resume experiences** to each question appropriately
- **Use the STAR method** for behavioral questions (Situation, Task, Action, Result)
- **Incorporate company context** from research when relevant
- **Demonstrate cultural fit** by aligning with company values
- **Show authentic personality** while maintaining professionalism
- **Include quantifiable achievements** when possible
- **Address the question directly** without generic fluff

Create answers that sound authentic and personalized, not like generic interview prep."""

ANSWER_USER_PROMPT_TEMPLATE = """Create a personalized answer for this interview question:

**QUESTION:** {question_text}
**CATEGORY:** {question_category}
**DIFFICULTY:** {question_difficulty}
**RATIONALE:** {question_rationale}

**ANSWER STRATEGY FROM PLANNER:**
Experience Highlights: {experience_highlights}
Skill Demonstration Opportunities: {skill_demonstration_opportunities}
Storytelling Approach: {storytelling_approach}
Answer Length Preference: {answer_length_preference}
Include Metrics: {include_metrics}
Company Values Integration: {company_values_integration}

**COMPANY & ROLE CONTEXT:**
Company: {company}
Role: {role}
Job Description Focus: {job_focus}

**RESEARCH FINDINGS:**
{research_context}

**CANDIDATE BACKGROUND:**
{resume_context}

**QUESTION ANALYSIS INSIGHTS:**
{question_insights}

Generate a compelling, personalized answer that directly addresses what the interviewer is evaluating and demonstrates authentic personality."""
