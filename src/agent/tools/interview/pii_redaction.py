"""PII redaction pipeline with security guardrails using Microsoft Presidio."""

import logging
import os
import re
from typing import Dict, List, Optional

from src.models.interview import PIIRedactionResult

logger = logging.getLogger(__name__)


class PIIRedactionPipeline:
    """PII redaction pipeline with security guardrails using Microsoft Presidio."""

    def __init__(self):
        """Initialize the PII redaction pipeline with lazy Presidio loading."""
        self.presidio_available = None  # None = not tested yet, True/False = tested
        self.analyzer = None
        self.anonymizer = None

        # Always initialize regex fallback patterns as safety net
        self._init_regex_fallback()
        logger.info("PII redaction pipeline initialized")

    def _init_regex_fallback(self):
        """Initialize regex-based fallback patterns for phone numbers and email only."""
        self.regex_patterns = {
            "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "PHONE": re.compile(
                r"(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})"
            ),
        }
        logger.info("Regex fallback patterns initialized")

    def _try_init_presidio(self):
        """Lazily initialize Presidio engines on first use."""
        if self.presidio_available is not None:
            return  # Already tested

        # Check for environment variable to use regex-only mode (for testing/debugging)
        if os.getenv("FORCE_REGEX_PII", "false").lower() in ("true", "1", "yes"):
            logger.info("FORCE_REGEX_PII set - using regex-only PII detection")
            self.presidio_available = False
            return

        try:
            logger.info("Initializing Presidio PII detection...")

            # Import Presidio modules
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine
            from presidio_anonymizer.entities import OperatorConfig

            # Create NLP engine configuration with the specific spaCy model
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }

            # Create NLP engine provider with our configuration
            nlp_engine_provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = nlp_engine_provider.create_engine()

            # Initialize Presidio engines
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            self.anonymizer = AnonymizerEngine()

            # Test Presidio functionality
            test_result = self.analyzer.analyze(
                text="test email: test@example.com", language="en"
            )

            # Configure anonymization operators for phone numbers and email only
            self.anonymization_config = {
                "EMAIL_ADDRESS": OperatorConfig(
                    "replace", {"new_value": "[REDACTED_EMAIL]"}
                ),
                "PHONE_NUMBER": OperatorConfig(
                    "replace", {"new_value": "[REDACTED_PHONE]"}
                ),
            }

            # Supported entity types for detection (phone numbers and email only)
            self.entity_types = [
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
            ]

            self.presidio_available = True
            logger.info("Presidio PII redaction initialized successfully")

        except Exception as e:
            logger.warning(f"Presidio unavailable: {e}")
            logger.info("Falling back to regex-based PII detection")
            self.presidio_available = False
            self.analyzer = None
            self.anonymizer = None

    def redact_resume(self, resume_text: str) -> PIIRedactionResult:
        """Redact PII from resume text using Presidio or regex fallback."""
        # Lazy initialization of Presidio on first use
        self._try_init_presidio()

        if self.presidio_available:
            return self._redact_with_presidio(resume_text)
        else:
            return self._redact_with_regex(resume_text)

    def _redact_with_presidio(self, resume_text: str) -> PIIRedactionResult:
        """Redact PII using Presidio engines."""
        logger.info("Starting Presidio PII redaction process")

        redaction_log = ["Starting Presidio PII redaction"]
        redactions_map = {}

        try:
            # Analyze text for PII entities
            analysis_results = self.analyzer.analyze(
                text=resume_text, entities=self.entity_types, language="en"
            )

            redaction_log.append(f"Found {len(analysis_results)} PII entities")
            logger.info(f"Presidio detected {len(analysis_results)} PII entities")

            # Create redactions map for transparency
            for i, result in enumerate(analysis_results):
                entity_type = result.entity_type
                confidence = result.score
                start = result.start
                end = result.end
                original_text = resume_text[start:end]

                redaction_key = self.anonymization_config[entity_type].params[
                    "new_value"
                ]
                redactions_map[f"{redaction_key}_{i}"] = (
                    f"{entity_type}: {len(original_text)} chars, confidence: {confidence:.2f}"
                )

                redaction_log.append(
                    f"Detected {entity_type} (confidence: {confidence:.2f})"
                )

            # Anonymize the text
            anonymized_result = self.anonymizer.anonymize(
                text=resume_text,
                analyzer_results=analysis_results,
                operators=self.anonymization_config,
            )

            redacted_text = anonymized_result.text

            # Validate redaction completeness
            complete = self._validate_redaction_complete(
                redacted_text, analysis_results
            )

            redaction_log.append(f"Redaction complete: {complete}")
            logger.info(f"Presidio PII redaction completed. Complete: {complete}")

            return PIIRedactionResult(
                redacted_resume_text=redacted_text,
                redactions_map=redactions_map,
                complete=complete,
                redaction_log=redaction_log,
            )

        except Exception as e:
            error_msg = f"Presidio PII redaction failed: {str(e)}"
            logger.error(error_msg)
            redaction_log.append(error_msg)

            # Fallback to regex if Presidio fails
            return self._redact_with_regex(resume_text)

    def _redact_with_regex(self, resume_text: str) -> PIIRedactionResult:
        """Fallback regex-based PII redaction."""
        logger.info("Starting regex-based PII redaction")

        redaction_log = ["Starting regex-based PII redaction (fallback)"]
        redactions_map = {}
        redacted_text = resume_text

        try:
            # Apply regex patterns
            for pii_type, pattern in self.regex_patterns.items():
                matches = pattern.findall(redacted_text)
                for i, match in enumerate(matches):
                    if isinstance(match, tuple):
                        # For phone numbers, we need to find the full match, not just the groups
                        if pii_type == "PHONE":
                            full_phone_pattern = re.compile(
                                r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
                            )
                            full_match = full_phone_pattern.search(redacted_text)
                            if full_match:
                                match_str = full_match.group()
                            else:
                                match_str = "".join(match)
                        else:
                            match_str = "".join(match)
                    else:
                        match_str = match

                    redaction_token = f"[REDACTED_{pii_type}_{len(redactions_map)}]"
                    redactions_map[redaction_token] = (
                        f"{pii_type}: {len(match_str)} chars"
                    )
                    redacted_text = redacted_text.replace(match_str, redaction_token, 1)
                    redaction_log.append(f"Detected {pii_type}")

            # Simple validation - check if obvious patterns remain
            complete = self._validate_regex_redaction(redacted_text)

            redaction_log.append(f"Regex redaction complete: {complete}")
            logger.info(f"Regex PII redaction completed. Complete: {complete}")

            return PIIRedactionResult(
                redacted_resume_text=redacted_text,
                redactions_map=redactions_map,
                complete=complete,
                redaction_log=redaction_log,
            )

        except Exception as e:
            error_msg = f"Regex PII redaction failed: {str(e)}"
            logger.error(error_msg)
            redaction_log.append(error_msg)

            return PIIRedactionResult(
                redacted_resume_text=resume_text,
                redactions_map={},
                complete=False,
                redaction_log=redaction_log,
            )

    def _validate_redaction_complete(
        self, redacted_text: str, analysis_results
    ) -> bool:
        """Validate that Presidio PII redaction is complete."""
        try:
            # Re-analyze the redacted text to check if any PII remains
            validation_results = self.analyzer.analyze(
                text=redacted_text, entities=self.entity_types, language="en"
            )

            # Check for high-confidence PII entities that might have been missed
            high_confidence_remaining = [
                result
                for result in validation_results
                if result.score > 0.7  # High confidence threshold
            ]

            if high_confidence_remaining:
                logger.warning(
                    f"Found {len(high_confidence_remaining)} high-confidence PII entities in redacted text"
                )
                return False

            # Additional basic pattern checks for phone numbers and email that might slip through
            suspicious_patterns = [
                (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
                (
                    r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
                    "phone number",
                ),
            ]

            for pattern, pii_type in suspicious_patterns:
                if re.search(pattern, redacted_text, re.IGNORECASE):
                    logger.warning(f"Found potential unredacted {pii_type} in text")
                    return False

            logger.info("PII redaction validation passed")
            return True

        except Exception as e:
            logger.warning(f"Redaction validation failed: {e}, assuming incomplete")
            return False

    def _validate_regex_redaction(self, redacted_text: str) -> bool:
        """Validate regex-based redaction completeness."""
        # Check if any of the regex patterns still match
        for pii_type, pattern in self.regex_patterns.items():
            if pattern.search(redacted_text):
                logger.warning(f"Found unredacted {pii_type} in text")
                return False

        logger.info("Regex redaction validation passed")
        return True


# Global instance for use across the application
pii_pipeline = PIIRedactionPipeline()
