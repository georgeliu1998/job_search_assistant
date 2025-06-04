#!/usr/bin/env python3
"""
Simple script to run the Job Search Assistant Streamlit app
"""

import os
import subprocess
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and guide user if not"""
    env_file = Path(".env")
    env_example = Path("env.example")

    if not env_file.exists():
        print("⚠️  No .env file found!")
        print("\n🔧 Setup Instructions:")
        print("1. Copy the example file:")
        print("   cp env.example .env")
        print("2. Edit .env and add your Anthropic API key")
        print("3. Run this script again")

        if env_example.exists():
            print(f"\n📄 Example file location: {env_example.absolute()}")

        return False

    # Check if API key is configured
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("⚠️  Please configure your ANTHROPIC_API_KEY in the .env file")
        print(f"📄 Edit: {env_file.absolute()}")
        return False

    print("✅ Environment configuration looks good!")
    return True


def main():
    """Main function to run the app"""
    print("🚀 Starting Job Search Assistant...")

    # Check environment setup
    if not check_env_file():
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
