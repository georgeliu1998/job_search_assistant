from langchain_core.prompts import PromptTemplate

JOB_INFO_EXTRACTION_RAW_TEMPLATE = """
You are tasked with extracting specific job information from a given job posting and presenting it in a structured JSON format. Here's the job posting you need to analyze:

<job_posting>
{job_text}
</job_posting>

Please extract the following information from the job posting:

1. Job Title: Extract the exact job title as written in the posting.

2. Company Name: Extract the company name if mentioned in the posting.

3. Salary Range: If mentioned, extract the minimum and maximum salary as numbers. If only one number is mentioned, use it as the maximum. If no salary information is provided, use null values.

4. Location/Remote Policy: Determine if the job is remote, hybrid, onsite, or if the policy is unclear based on the information provided.

5. Role Type: Identify if the role is for an Individual Contributor (IC), Manager, or if it's unclear based on the job description.

After analyzing the job posting, present the extracted information in the following JSON format:

{{
  "title": "Exact title as written",
  "company": "Company name or null if not provided",
  "salary_min": minimum salary (number or null if not provided),
  "salary_max": maximum salary (number or null if not provided),
  "location_policy": "remote/hybrid/onsite/unclear",
  "role_type": "ic/manager/unclear"
}}

Important guidelines:
- Base your extraction solely on the information provided in the job posting.
- If any information is not explicitly mentioned or is ambiguous, use "unclear" or null values as appropriate.
- For salary values, use null if not provided. If only one number is mentioned, use it as the maximum and set the minimum to null.
- For location_policy and role_type, use lowercase values: "remote", "hybrid", "onsite", "unclear", "ic", "manager"
- Be precise in your extraction, avoiding any assumptions or inferences not directly supported by the text.

Please provide your final output in the specified JSON format without any explanations.
"""

JOB_INFO_EXTRACTION_PROMPT = PromptTemplate.from_template(
    JOB_INFO_EXTRACTION_RAW_TEMPLATE
)
