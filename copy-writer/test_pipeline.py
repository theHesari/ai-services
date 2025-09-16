#!/usr/bin/env python3
"""
Simple test script for the Content Pipeline
Run this to test the pipeline without the FastAPI server
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
load_dotenv()


def test_pipeline():
    """Test the content pipeline with a simple request"""

    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("💡 Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY=your_api_key_here")
        print("   or create a .env file with: OPENAI_API_KEY=your_api_key_here")
        return False

    try:
        from src.workflows.content_pipeline import ContentPipeline
        from src.models.content_models import ContentRequest, ContentType, Priority

        print("🔧 Initializing Content Pipeline...")
        pipeline = ContentPipeline(
            openai_api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("OPENAI_MODEL"),
        )
        print("✅ Pipeline initialized successfully!")

        # Create a simple test request
        test_request = ContentRequest(
            topic="How to improve productivity",
            content_type=ContentType.BLOG_POST,
            priority=Priority.MEDIUM,
            target_audience="professionals",
            tone="professional",
            length="short",
        )

        print("📝 Processing test request...")
        result = pipeline.process_request(test_request)

        if result and result.get("success"):
            print("✅ Test successful!")
            print(f"📊 Quality Score: {result['quality_report']['overall_score']}")
            print(f"📝 Word Count: {result['draft']['word_count']}")
            print(f"🎯 Requires Review: {result['requires_human_review']}")
            return True
        else:
            error_msg = (
                result.get("error", "Unknown error")
                if result
                else "Pipeline returned None"
            )
            print(f"❌ Test failed: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Content Writer Pipeline...")
    print("=" * 50)

    success = test_pipeline()

    if success:
        print("\n✅ All tests passed! The pipeline is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
