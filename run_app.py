#!/usr/bin/env python3
"""
Main entry point for the Job Search Assistant application.

This script provides a simple CLI interface to run different components
of the job search assistant system.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def main():
    """Main entry point for the application."""
    print("🚀 Job Search Assistant")
    print("=" * 50)

    try:
        # Test basic imports
        from src.agents.job_evaluation import JobEvaluationAgent
        from src.config import config

        print("✅ All modules imported successfully")

        # Load configuration
        print(f"✅ Configuration loaded for environment: {config.general.name}")

        # Initialize job evaluation agent
        agent = JobEvaluationAgent()
        print("✅ Job evaluation agent initialized")

        print("\n🎉 Application startup successful!")
        print("\nNext steps:")
        print("1. Set APP_ENV environment variable (dev, stage, or prod)")
        print("2. Set required API keys in environment variables")
        print("3. Use the JobEvaluationAgent to evaluate job postings")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the project root directory")
        print("2. Install dependencies: uv sync")
        print("3. Check that all required files are present")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nTroubleshooting:")
        print("1. Set APP_ENV environment variable (dev, stage, or prod)")
        print("2. Check that config files exist in configs/ directory")
        print("3. Set required API keys:")
        print("   - ANTHROPIC_API_KEY")
        print("   - LANGFUSE_PUBLIC_KEY (optional)")
        print("   - LANGFUSE_SECRET_KEY (optional)")
        sys.exit(1)


if __name__ == "__main__":
    main()
