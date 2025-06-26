"""
Environment check component for validating configuration
"""

import streamlit as st

from src.config import config


def check_environment_setup() -> tuple[bool, str]:
    """Check if the environment is properly configured"""
    try:
        # Check if configs can be loaded
        # config is already imported at module level

        # Check if at least one LLM profile has an API key
        has_valid_profile = False
        for profile_name, profile in config.llm_profiles.items():
            if profile.api_key:
                has_valid_profile = True
                break

        if not has_valid_profile:
            return False, "No LLM profiles have valid API keys configured"

        return True, "Environment is properly configured"
    except Exception as e:
        return False, f"Configuration error: {str(e)}"


def render_environment_warning():
    """Render environment setup warning if needed"""
    env_ok, env_message = check_environment_setup()
    if not env_ok:
        st.error(f"⚠️ **Setup Required:** {env_message}")
        st.info(
            """
        **Setup Instructions:**
        1. Create a `.env` file in the root directory
        2. Add your Anthropic API key: `ANTHROPIC_API_KEY=your_key_here`
        3. Restart the Streamlit app

        Optional: Add Langfuse keys for observability:
        - `LANGFUSE_PUBLIC_KEY=your_public_key`
        - `LANGFUSE_SECRET_KEY=your_secret_key`
        - `LANGFUSE_ENABLED=true`
        """
        )
    return env_ok
