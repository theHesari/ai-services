from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import time
from dotenv import load_dotenv

from src.workflows.content_pipeline import ContentPipeline
from src.models.content_models import ContentRequest
from config.logging_config import get_logger, get_pipeline_logger

# Load environment variables
load_dotenv()

# Initialize logging
logger = get_logger(__name__)
pipeline_logger = get_pipeline_logger()

app = FastAPI(title="Content Writer Agent", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    pipeline_logger.log_api_request(
        endpoint=request.url.path,
        method=request.method,
        request_id=request.headers.get("X-Request-ID"),
    )

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    pipeline_logger.log_api_response(
        endpoint=request.url.path,
        status_code=response.status_code,
        response_time=process_time,
        request_id=request.headers.get("X-Request-ID"),
    )

    return response


# Initialize content pipeline
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY environment variable not set!")
    logger.error(
        "Please create a .env file with your OpenAI API key: OPENAI_API_KEY=your_openai_api_key_here"
    )
    exit(1)

logger.info("Initializing Content Pipeline...")
try:
    pipeline = ContentPipeline(openai_api_key=openai_api_key)
    logger.info("✅ Content Pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Content Pipeline: {e}")
    raise


# API Models
class ContentRequestAPI(BaseModel):
    topic: str
    content_type: str = "blog_post"
    priority: str = "medium"
    target_audience: Optional[str] = None
    key_points: Optional[list] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    seo_keywords: Optional[list] = None
    brand_voice: Optional[str] = None
    additional_context: Optional[str] = None


class FeedbackModel(BaseModel):
    approved: bool
    feedback_text: Optional[str] = None
    suggested_changes: Optional[list] = None
    quality_rating: Optional[int] = None


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Content Writer Agent API", "version": "1.0.0"}


@app.post("/content/create")
async def create_content(request: ContentRequestAPI):
    """Create content from request"""
    request_id = None

    try:
        logger.info(
            f"Content creation request received: {request.topic} ({request.content_type})"
        )

        # Convert API model to internal model
        content_request = ContentRequest(**request.model_dump())
        request_id = content_request.request_id

        logger.info(f"Processing content request: {request_id}")

        # Process through pipeline
        result = pipeline.process_request(content_request)

        if result.get("success"):
            logger.info(f"Content created successfully: {request_id}")
        else:
            logger.error(
                f"Content creation failed: {request_id} - {result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Error in create_content endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/content/{request_id}/feedback")
async def submit_feedback(request_id: str, feedback: FeedbackModel):
    """Submit feedback for content"""

    try:
        logger.info(
            f"Feedback received for request: {request_id} (approved: {feedback.approved})"
        )

        feedback_dict = feedback.model_dump()
        result = pipeline.process_feedback(request_id, feedback_dict)

        if result.get("success"):
            logger.info(f"Feedback processed successfully: {request_id}")
        else:
            logger.error(
                f"Feedback processing failed: {request_id} - {result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Error in submit_feedback endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/{request_id}/status")
async def get_content_status(request_id: str):
    """Get status of content request"""

    try:
        logger.info(f"Status request for: {request_id}")

        status = pipeline.get_content_status(request_id)

        if not status["found"]:
            logger.warning(f"Content not found: {request_id}")
            raise HTTPException(status_code=404, detail="Content not found")

        logger.info(f"Status retrieved for: {request_id} - {status.get('status')}")
        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_content_status endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/performance")
async def get_performance_analytics():
    """Get content performance analytics"""

    try:
        logger.info("Performance analytics requested")

        metrics = pipeline.content_history.get_performance_metrics()

        logger.info(
            f"Performance metrics retrieved: {len(metrics) if isinstance(metrics, dict) else 'N/A'} metrics"
        )
        return metrics

    except Exception as e:
        logger.error(f"Error in get_performance_analytics endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# CLI interface for testing
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Content Writer Agent...")

    # Test the system with a sample request
    logger.info("🧪 Testing with sample request...")

    sample_request = ContentRequest(
        topic="How to improve productivity while working from home",
        content_type="blog_post",
        target_audience="remote workers and freelancers",
        key_points=[
            "Setting up a dedicated workspace",
            "Managing distractions",
            "Maintaining work-life balance",
        ],
        tone="helpful and practical",
        length="medium",
    )

    try:
        result = pipeline.process_request(sample_request)

        if result and result.get("success"):
            logger.info("✅ Sample content created successfully!")
        else:
            error_msg = (
                result.get("error", "Unknown error")
                if result
                else "Pipeline returned None"
            )
            logger.error(f"❌ Error: {error_msg}")

    except Exception as e:
        logger.error(f"❌ Error testing system: {e}", exc_info=True)
        import traceback

        traceback.print_exc()

    # Start the API server
    logger.info("🌐 Starting API server on http://127.0.0.1:8001")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
