#!/usr/bin/env python3
"""
Example script demonstrating Langfuse tracing integration.

This script shows how to use the context-aware tracing system
and can be used to test your tracing setup.

Usage:
    # Set up environment first
    export LANGFUSE_PUBLIC_KEY=pk-lf-your-key
    export LANGFUSE_SECRET_KEY=sk-lf-your-key
    export APP_ENV=dev

    # Run the example
    python docs/examples/tracing-example.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment for demo
os.environ.setdefault("APP_ENV", "dev")

from src.agent.workflows.job_evaluation import run_job_evaluation_workflow
from src.llm import langfuse_manager


def demonstrate_tracing():
    """Demonstrate the tracing system with real examples."""

    print("🔍 Langfuse Tracing Example")
    print("=" * 40)

    # Check tracing status
    if langfuse_manager.is_enabled():
        print("✅ Langfuse tracing is ENABLED")
        handler = langfuse_manager.get_handler()
        print(f"✅ Handler available: {handler is not None}")
    else:
        print("❌ Langfuse tracing is DISABLED")
        print("💡 To enable:")
        print("   1. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        print("   2. Set observability.langfuse.enabled=true in config")
        print("   3. Ensure APP_ENV is set to 'dev' or 'prod'")
        return

    print("\n📋 Testing Context-Aware Tracing")
    print("-" * 30)

    # Example job posting
    job_posting = """
    Senior AI Engineer at TechCorp
    Remote - $150,000 - $200,000

    We're looking for a Senior AI Engineer to join our team.
    This is a fully remote position working on cutting-edge AI systems.

    Requirements:
    - 5+ years of experience in AI/ML
    - Python expertise
    - Experience with LLMs
    """

    print("📝 Sample job posting:")
    print(job_posting.strip()[:100] + "...")

    print("\n🚀 Running workflow with tracing...")
    try:
        # This will use get_workflow_config() internally
        result = run_job_evaluation_workflow(job_posting)

        print(f"✅ Workflow completed!")
        print(f"📊 Recommendation: {result.recommendation}")
        print(f"💭 Reasoning: {result.reasoning[:100]}...")

        if langfuse_manager.is_enabled():
            print("\n🎯 Tracing Results:")
            print("- Check your Langfuse dashboard for a single, clean workflow trace")
            print("- Individual LLM calls are nested within the workflow trace")
            print("- No duplicate traces should appear")

    except Exception as e:
        print(f"❌ Error running workflow: {e}")
        print("💡 This might be due to missing API keys or configuration issues")

    print("\n" + "=" * 40)
    print("Example complete! 🎉")


def demonstrate_api_methods():
    """Show examples of different API methods."""

    print("\n🔧 API Method Examples")
    print("-" * 25)

    # Workflow config
    workflow_config = langfuse_manager.get_workflow_config()
    print(f"📈 Workflow config: {list(workflow_config.keys())}")

    # Individual call config (context-aware)
    call_config = langfuse_manager.get_config()
    print(f"🔍 Call config: {list(call_config.keys())}")

    # Forced tracing
    forced_config = langfuse_manager.get_config(force_tracing=True)
    print(f"⚡ Forced config: {list(forced_config.keys())}")

    # With additional config
    custom_config = langfuse_manager.get_config({"temperature": 0.7})
    print(f"⚙️  Custom config: {list(custom_config.keys())}")


if __name__ == "__main__":
    try:
        demonstrate_tracing()
        demonstrate_api_methods()

    except KeyboardInterrupt:
        print("\n\n👋 Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Make sure you're running from the project root directory")
        sys.exit(1)
