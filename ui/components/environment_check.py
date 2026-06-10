"""
Environment check component for validating configuration
"""

import streamlit as st

from src.config import config


def get_missing_api_keys() -> set[str]:
    """Return the set of API-key env var names required by configured tasks
    that are currently missing."""
    missing_keys: set[str] = set()
    for _task_name, agent_llm in vars(config.agent_tasks).items():
        if not agent_llm.api_key:
            provider = agent_llm.provider.upper()
            missing_keys.add(f"{provider}_API_KEY")
    return missing_keys


def check_environment_setup() -> tuple[bool, str]:
    """Check if the environment is properly configured"""
    try:
        missing_keys = get_missing_api_keys()
        if missing_keys:
            missing_str = ", ".join(sorted(missing_keys))
            return False, f"Missing required API keys: {missing_str}"

        return True, "Environment is properly configured"
    except Exception as e:
        return False, f"Configuration error: {str(e)}"


def build_setup_instructions(missing_keys: set[str]) -> str:
    """Build setup instructions that reference the actual missing API keys.

    Keeps the instructions in sync with what the detector reports, so users
    don't get told to configure a provider that the app isn't actually using.
    """
    if missing_keys:
        sorted_keys = sorted(missing_keys)
        key_lines = "\n".join(f"   - `{name}=your_key_here`" for name in sorted_keys)
        keys_section = "2. Add the missing API key(s) listed above:\n" + key_lines
    else:
        keys_section = "2. Add the required API key(s) for your configured providers"

    return f"""
**Setup Instructions:**
1. Create a `.env` file in the root directory
{keys_section}
3. Restart the Streamlit app

Optional: Add Langfuse keys for observability:
- `LANGFUSE_PUBLIC_KEY=your_public_key`
- `LANGFUSE_SECRET_KEY=your_secret_key`
- `LANGFUSE_ENABLED=true`
"""


def render_environment_warning():
    """Render environment setup warning if needed"""
    env_ok, env_message = check_environment_setup()
    if not env_ok:
        st.error(f"⚠️ **Setup Required:** {env_message}")
        try:
            missing_keys = get_missing_api_keys()
        except Exception:
            missing_keys = set()
        st.info(build_setup_instructions(missing_keys))
    return env_ok
