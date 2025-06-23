#!/usr/bin/env python3
"""
Simple script to run the Job Search Assistant Streamlit app
"""

import os
import subprocess
import sys
from pathlib import Path


def check_env_setup():
    """Check if environment is properly configured using centralized configs"""
    # Set APP_ENV if not already set
    if "APP_ENV" not in os.environ:
        os.environ["APP_ENV"] = "dev"

    try:
        # Try to load configs to validate configuration
        from src.config import configs

        # Check if at least one LLM profile has an API key
        has_valid_profile = False
        for profile_name, profile in configs.llm_profiles.items():
            if profile.api_key:
                has_valid_profile = True
                break

        if not has_valid_profile:
            print("⚠️  No LLM profiles have valid API keys configured!")
            print("\n🔧 Setup Instructions:")
            print("1. Set APP_ENV environment variable (dev, test, or prod)")
            print("2. Add your API keys to environment variables:")
            print("   - ANTHROPIC_API_KEY=your_anthropic_key")
            print("   - FIREWORKS_API_KEY=your_fireworks_key (optional)")
            print("3. Run this script again")
            return False

        print("✅ Configuration loaded successfully!")
        print(f"📋 Active environment: {os.getenv('APP_ENV', 'dev')}")
        print(f"🤖 Available LLM profiles: {', '.join(configs.llm_profiles.keys())}")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Setup Instructions:")
        print("1. Set APP_ENV environment variable: export APP_ENV=dev")
        print("2. Ensure configuration files exist in configs/ directory")
        print("3. Add your API keys to environment variables")
        return False


def main():
    """Main function to run the app"""
    print("🚀 Starting Job Search Assistant...")

    # Check environment setup
    if not check_env_setup():
        sys.exit(1)

    # Run the Streamlit app
    try:
        print("🌐 Starting Streamlit server...")
        print("📱 The app will open in your browser automatically")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)

        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "ui/app.py",
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ]
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error running the app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
