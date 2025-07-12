"""
Job posting extraction prompt for structured outputs.

This prompt is optimized for use with LangChain's structured outputs feature,
focusing on clear instructions without JSON formatting requirements.
"""

from langchain_core.prompts import PromptTemplate

JOB_POSTING_EXTRACTION_RAW_TEMPLATE = """
You are tasked with extracting specific job information from a given job posting. Here's the job posting you need to analyze:

<job_posting>
{job_text}
</job_posting>

Please extract the following information from the job posting:

1. **Job Title**: Extract the exact job title as written in the posting.

2. **Company Name**: Extract the company name if mentioned in the posting.

3. **Salary Range**: If mentioned, extract the minimum and maximum salary as numbers (annual, in USD). If only one number is mentioned, use it as the maximum. If no salary information is provided, leave as null.

4. **Location/Remote Policy**: Determine if the job is:
   - "remote": Fully remote work
   - "hybrid": Mix of remote and office work
   - "onsite": Must work from office/specific location
   - "unclear": Policy not clearly stated

5. **Role Type**: Identify if the role is:
   - "ic": Individual Contributor (non-management role)
   - "manager": Management/leadership role
   - "unclear": Role type not clearly indicated

Important guidelines:
- Base your extraction solely on the information provided in the job posting
- If any information is not explicitly mentioned or is ambiguous, use "unclear" or null values as appropriate
- For salary values, use null if not provided. If only one number is mentioned, use it as the maximum and set the minimum to null
- Be precise in your extraction, avoiding assumptions or inferences not directly supported by the text
- Look for keywords like "remote", "hybrid", "on-site", "manager", "lead", "senior" to help classify location policy and role type
"""

JOB_POSTING_EXTRACTION_PROMPT = PromptTemplate.from_template(
    JOB_POSTING_EXTRACTION_RAW_TEMPLATE
)
