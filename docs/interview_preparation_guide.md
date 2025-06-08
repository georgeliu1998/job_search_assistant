# Interview Preparation Feature Guide

The Interview Preparation Assistant helps you prepare for job interviews by generating personalized, comprehensive interview guides based on your specific situation.

## Features

- **Personalized Questions**: Get likely interview questions based on the job description and interview type
- **Suggested Answers**: Receive tailored answer frameworks based on your resume and experience
- **Company Insights**: Analysis of the company and role to help you demonstrate fit
- **Interview Strategy**: Specific advice for your interview type and situation
- **Questions to Ask**: Thoughtful questions to ask the interviewer
- **PDF Support**: Upload your resume and LinkedIn profiles as PDFs

## How to Use

### 1. Required Information

- **Job Description**: Paste the complete job posting
- **Interview Type**: Select from:
  - HR pre-screen
  - Hiring manager interview
  - Technical interview
- **Resume**: Upload PDF or paste text

### 2. Optional Details (Recommended)

- **Interviewer Name & Title**: Helps personalize the preparation
- **Company Website**: Provides additional context for insights
- **Interviewer LinkedIn**: Upload PDF or paste profile information

### 3. Generate Your Guide

Click "Generate Interview Guide" and wait for your personalized preparation materials.

## Setup Requirements

### API Key Setup

You need a Google Gemini API key to use this feature:

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your environment:
   - **Option A**: Add to `.env` file: `GEMINI_API_KEY=your_key_here`
   - **Option B**: Add to Streamlit secrets (for deployment)

### Cost Information

Based on [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing):

- **Model Used**: Gemini 2.5 Flash (cost-effective choice)
- **Typical Cost**: $0.01-0.05 per interview guide
- **Free Tier**: Available for testing and light usage

## Example Output

Your interview guide will include:

### 1. Interview Overview & Strategy
- What to expect for your specific interview type
- Key success factors and recommended approach
- Preparation timeline

### 2. Likely Interview Questions & Suggested Answers
- 8-12 personalized questions based on the role
- Answer frameworks tailored to your background
- Key points to emphasize from your experience

### 3. Company & Role Insights
- Analysis of the company and position
- Talking points to demonstrate fit
- Cultural alignment opportunities

### 4. Questions to Ask the Interviewer
- 5-7 thoughtful questions for your interview type
- Questions that show preparation and genuine interest

### 5. Final Preparation Tips
- Interview-specific advice
- Confidence boosters and key reminders
- Last-minute preparation checklist

### 6. Interview Day Strategy
- What to bring and how to prepare
- Making a strong first impression
- Closing the interview effectively

## Tips for Best Results

1. **Provide Complete Information**: The more context you provide, the better your guide will be
2. **Use the Full Job Description**: Include requirements, responsibilities, and company info
3. **Upload Your Complete Resume**: More experience details = better personalized answers
4. **Include Interviewer Details**: Helps tailor questions and approach
5. **Review and Practice**: Use the guide as a starting point, then practice your answers

## Troubleshooting

### Common Issues

- **API Key Error**: Verify your Gemini API key is correct and has quota remaining
- **PDF Upload Issues**: Ensure PDFs are text-based (not scanned images)
- **Long Generation Time**: Complex guides may take 30-60 seconds to generate

### Getting Help

If you encounter issues:
1. Check the error message for specific guidance
2. Verify your API key setup
3. Try with a simpler input to test the system
4. Check the GitHub repository for known issues

## Privacy & Security

- Your data is sent to Google's Gemini API for processing
- No data is stored permanently by the application
- Resume and job description data is only used for guide generation
- Consider using anonymized versions of sensitive documents for testing
