"""Unit tests for LLM prompts module."""

import pytest
from langchain_core.prompts import PromptTemplate

from src.llm.prompts.job_evaluation.extraction import (
    JOB_INFO_EXTRACTION_PROMPT,
    JOB_INFO_EXTRACTION_RAW_TEMPLATE,
)


class TestJobInfoExtractionPrompt:
    """Test the job information extraction prompt."""

    def test_raw_template_is_string(self):
        """Test that the raw template is a string."""
        assert isinstance(JOB_INFO_EXTRACTION_RAW_TEMPLATE, str)
        assert len(JOB_INFO_EXTRACTION_RAW_TEMPLATE) > 0

    def test_prompt_is_prompt_template(self):
        """Test that the prompt is a PromptTemplate instance."""
        assert isinstance(JOB_INFO_EXTRACTION_PROMPT, PromptTemplate)

    def test_prompt_has_correct_input_variables(self):
        """Test that the prompt has the correct input variables."""
        expected_variables = ["job_text"]
        assert JOB_INFO_EXTRACTION_PROMPT.input_variables == expected_variables

    def test_prompt_template_contains_job_text_placeholder(self):
        """Test that the raw template contains the job_text placeholder."""
        assert "{job_text}" in JOB_INFO_EXTRACTION_RAW_TEMPLATE

    def test_prompt_template_structure_content(self):
        """Test that the template contains expected structural elements."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for key sections
        assert "<job_posting>" in template
        assert "</job_posting>" in template
        assert "JSON format" in template
        assert "Job Title" in template
        assert "Company Name" in template
        assert "Salary Range" in template
        assert "Location/Remote Policy" in template
        assert "Role Type" in template

    def test_prompt_template_json_structure(self):
        """Test that the template contains proper JSON structure."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for JSON fields
        assert '"title":' in template
        assert '"company":' in template
        assert '"salary_min":' in template
        assert '"salary_max":' in template
        assert '"location_policy":' in template
        assert '"role_type":' in template

    def test_prompt_template_guidelines(self):
        """Test that the template contains important guidelines."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for important guidelines
        assert "Important guidelines:" in template
        assert "null" in template  # For handling missing values
        assert "unclear" in template  # For ambiguous information
        assert "remote" in template
        assert "hybrid" in template
        assert "onsite" in template
        assert "ic" in template  # Individual Contributor
        assert "manager" in template

    def test_prompt_format_with_sample_job_text(self):
        """Test formatting the prompt with sample job text."""
        sample_job_text = """
        Software Engineer - Remote

        We are looking for a skilled software engineer to join our team.
        The role offers competitive salary and remote work options.
        """

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=sample_job_text)

        # Check that the job text was inserted correctly
        assert sample_job_text in formatted_prompt
        assert "<job_posting>" in formatted_prompt
        assert "</job_posting>" in formatted_prompt
        assert "Software Engineer - Remote" in formatted_prompt

    def test_prompt_format_with_empty_job_text(self):
        """Test formatting the prompt with empty job text."""
        empty_job_text = ""

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=empty_job_text)

        # Should still format correctly even with empty text
        assert "<job_posting>" in formatted_prompt
        assert "</job_posting>" in formatted_prompt
        assert formatted_prompt.count("<job_posting>") == 1
        assert formatted_prompt.count("</job_posting>") == 1

    def test_prompt_format_with_special_characters(self):
        """Test formatting the prompt with special characters in job text."""
        special_job_text = """
        Job Title: Senior Engineer @ Tech Corp
        Salary: $100,000 - $150,000
        Requirements: 5+ years experience
        Benefits: Health insurance & 401(k)
        """

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=special_job_text)

        # Special characters should be preserved
        assert "@" in formatted_prompt
        assert "$" in formatted_prompt
        assert "&" in formatted_prompt
        assert "+" in formatted_prompt

    def test_prompt_format_with_long_job_text(self):
        """Test formatting the prompt with very long job text."""
        long_job_text = "Very long job description. " * 1000  # Very long text

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=long_job_text)

        # Should handle long text without issues
        assert long_job_text in formatted_prompt
        assert len(formatted_prompt) > len(JOB_INFO_EXTRACTION_RAW_TEMPLATE)

    def test_template_instruction_clarity(self):
        """Test that the template provides clear instructions."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for clear instruction keywords
        assert "extract" in template.lower()
        assert "analyze" in template.lower()
        assert "present" in template.lower()
        assert "format" in template.lower()

    def test_template_field_descriptions(self):
        """Test that each field has proper description."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Each field should have a description
        fields_with_descriptions = [
            "Job Title:",
            "Company Name:",
            "Salary Range:",
            "Location/Remote Policy:",
            "Role Type:",
        ]

        for field in fields_with_descriptions:
            assert field in template

    def test_template_value_constraints(self):
        """Test that the template specifies value constraints."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for specific value constraints
        assert "remote/hybrid/onsite/unclear" in template
        assert "ic/manager/unclear" in template
        assert "lowercase" in template

    def test_template_null_handling_instructions(self):
        """Test that the template provides clear null handling instructions."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for null handling guidance
        assert "null" in template
        assert "not provided" in template
        assert "not explicitly mentioned" in template

    def test_template_output_format_specification(self):
        """Test that the template clearly specifies output format."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Should specify JSON output format
        assert "JSON format" in template
        assert "without any explanations" in template
        assert "final output" in template

    def test_prompt_template_creation_from_raw(self):
        """Test that the PromptTemplate is correctly created from raw template."""
        # Create a new template from the raw string
        new_template = PromptTemplate.from_template(JOB_INFO_EXTRACTION_RAW_TEMPLATE)

        # Should be equivalent to the exported one
        assert new_template.template == JOB_INFO_EXTRACTION_PROMPT.template
        assert (
            new_template.input_variables == JOB_INFO_EXTRACTION_PROMPT.input_variables
        )

    def test_template_formatting_consistency(self):
        """Test that template formatting is consistent."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Check for consistent formatting patterns
        lines = template.split("\n")

        # Should have proper structure
        assert any("You are tasked with" in line for line in lines)
        assert any("Please extract the following" in line for line in lines)
        assert any("After analyzing" in line for line in lines)

    def test_template_example_json_validity(self):
        """Test that the JSON example in template is structurally valid."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Find the JSON example section (skip the {job_text} placeholder)
        job_text_placeholder = template.find("{job_text}")
        search_start = (
            job_text_placeholder + len("{job_text}")
            if job_text_placeholder != -1
            else 0
        )

        json_start = template.find("{", search_start)
        json_end = template.find("}", json_start) + 1

        assert json_start != -1, "JSON example should be present"
        assert json_end != -1, "JSON example should be complete"

        json_example = template[json_start:json_end]

        # Check that it contains all required fields
        required_fields = [
            '"title":',
            '"company":',
            '"salary_min":',
            '"salary_max":',
            '"location_policy":',
            '"role_type":',
        ]
        for field in required_fields:
            assert field in json_example

    def test_prompt_partial_formatting(self):
        """Test partial formatting capabilities."""
        # Test that we can create a partial template
        partial_prompt = JOB_INFO_EXTRACTION_PROMPT.partial()

        # Should still be a PromptTemplate
        assert isinstance(partial_prompt, PromptTemplate)
        assert partial_prompt.input_variables == ["job_text"]

    def test_prompt_with_multiple_job_postings(self):
        """Test formatting with multiple job posting examples."""
        multiple_jobs = """
        Job 1: Software Engineer at Google
        Remote position, $120k-$180k

        Job 2: Product Manager at Facebook
        Hybrid work, San Francisco
        """

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=multiple_jobs)

        # Should handle multiple job descriptions
        assert "Job 1:" in formatted_prompt
        assert "Job 2:" in formatted_prompt
        assert "Google" in formatted_prompt
        assert "Facebook" in formatted_prompt

    def test_template_language_and_tone(self):
        """Test that the template uses appropriate language and tone."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Should be professional and clear
        assert "You are tasked with" in template  # Clear instruction
        assert "Please extract" in template  # Polite request
        assert "Important guidelines:" in template  # Clear structure

        # Should avoid ambiguous language
        assert "exactly" in template or "exact" in template
        assert "precise" in template or "precisely" in template

    def test_template_completeness(self):
        """Test that the template covers all necessary aspects."""
        template = JOB_INFO_EXTRACTION_RAW_TEMPLATE

        # Should cover all major job posting elements
        job_elements = [
            "title",
            "company",
            "salary",
            "location",
            "remote",
            "role",
            "manager",
        ]

        template_lower = template.lower()
        for element in job_elements:
            assert element in template_lower

    def test_error_handling_with_invalid_format_string(self):
        """Test behavior with invalid format strings."""
        # This should not raise an error during template creation
        template = JOB_INFO_EXTRACTION_PROMPT

        # But should raise KeyError when formatting with wrong variables
        with pytest.raises(KeyError):
            template.format(wrong_variable="test")

    def test_template_immutability(self):
        """Test that the template constants are not accidentally modified."""
        original_template = JOB_INFO_EXTRACTION_RAW_TEMPLATE
        original_prompt_template = JOB_INFO_EXTRACTION_PROMPT.template

        # These should remain the same throughout the test
        assert JOB_INFO_EXTRACTION_RAW_TEMPLATE == original_template
        assert JOB_INFO_EXTRACTION_PROMPT.template == original_prompt_template


class TestPromptModuleStructure:
    """Test the overall structure of the prompts module."""

    def test_module_exports(self):
        """Test that the module exports the expected constants."""
        from src.llm.prompts.job_evaluation import extraction

        # Should have the expected attributes
        assert hasattr(extraction, "JOB_INFO_EXTRACTION_RAW_TEMPLATE")
        assert hasattr(extraction, "JOB_INFO_EXTRACTION_PROMPT")

    def test_template_and_prompt_consistency(self):
        """Test that the raw template and PromptTemplate are consistent."""
        # The PromptTemplate should be created from the raw template
        assert JOB_INFO_EXTRACTION_PROMPT.template == JOB_INFO_EXTRACTION_RAW_TEMPLATE

    def test_prompt_template_type_safety(self):
        """Test type safety of prompt template."""
        # Should be proper types
        assert isinstance(JOB_INFO_EXTRACTION_RAW_TEMPLATE, str)
        assert isinstance(JOB_INFO_EXTRACTION_PROMPT, PromptTemplate)

        # Should not be empty
        assert JOB_INFO_EXTRACTION_RAW_TEMPLATE.strip()
        assert JOB_INFO_EXTRACTION_PROMPT.template.strip()


class TestPromptUsageScenarios:
    """Test realistic usage scenarios for the prompts."""

    def test_typical_job_posting_scenario(self):
        """Test with a typical job posting."""
        typical_job = """
        Senior Software Engineer
        TechCorp Inc.

        We are seeking a Senior Software Engineer to join our growing team.
        This is a full-time remote position.

        Salary: $130,000 - $160,000 per year

        Requirements:
        - 5+ years of experience
        - Python, JavaScript experience
        - Strong communication skills

        Benefits:
        - Health insurance
        - 401k matching
        - Flexible schedule
        """

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=typical_job)

        # Should contain all the job information
        assert "Senior Software Engineer" in formatted_prompt
        assert "TechCorp Inc." in formatted_prompt
        assert "$130,000 - $160,000" in formatted_prompt
        assert "remote" in formatted_prompt

    def test_minimal_job_posting_scenario(self):
        """Test with minimal job posting information."""
        minimal_job = "Software Engineer position available."

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=minimal_job)

        # Should still format correctly
        assert minimal_job in formatted_prompt
        assert "JSON format" in formatted_prompt

    def test_complex_job_posting_scenario(self):
        """Test with complex job posting with edge cases."""
        complex_job = """
        Lead Software Engineer / Engineering Manager
        ABC Corp (subsidiary of XYZ Holdings)

        Hybrid role: 3 days in office (San Francisco), 2 days remote

        Compensation Package:
        - Base salary: $150,000 - $200,000
        - Equity: 0.1% - 0.3%
        - Bonus: Up to 20% of base

        This role can be either IC (Individual Contributor) track or
        Management track depending on candidate preference.
        """

        formatted_prompt = JOB_INFO_EXTRACTION_PROMPT.format(job_text=complex_job)

        # Should handle complex scenarios
        assert "Lead Software Engineer" in formatted_prompt
        assert "Engineering Manager" in formatted_prompt
        assert "ABC Corp" in formatted_prompt
        assert "Hybrid" in formatted_prompt
        assert "$150,000 - $200,000" in formatted_prompt
