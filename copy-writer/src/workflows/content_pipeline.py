from langchain_openai import ChatOpenAI
from ..agents.router import ContentRouter
from ..agents.content_planner import ContentPlanner
from ..agents.content_writer import ContentWriter
from ..agents.quality_checker import QualityChecker
from ..models.content_models import ContentRequest, ContentDraft, QualityReport
from ..memory.content_history import ContentHistory
from ..memory.user_preferences import UserPreferences
from typing import Dict, Any, Optional
import uuid
import time
from datetime import datetime
from config.logging_config import (
    get_logger,
    log_pipeline_start,
    log_pipeline_step,
    log_pipeline_complete,
    log_agent_action,
    log_error,
    log_performance,
)


class ContentPipeline:
    def __init__(
        self,
        openai_api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.logger = get_logger(__name__)

        if not openai_api_key:
            self.logger.error("OpenAI API key is required")
            raise ValueError("OpenAI API key is required")

        self.logger.info("Initializing Content Pipeline components...")

        # Initialize LLM with configurable base URL
        llm_config = {
            "api_key": openai_api_key,
            "model": model or "gpt-4",
            "temperature": 0.7,
        }

        # Add base_url if provided (for OpenRouter, etc.)
        if base_url:
            llm_config["base_url"] = base_url

        try:
            self.logger.info(f"Initializing LLM with model: {llm_config['model']}")
            self.llm = ChatOpenAI(**llm_config)
            self.logger.info("✅ LLM initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ValueError(f"Failed to initialize OpenAI client: {e}")

        # Initialize agents
        self.logger.info("Initializing agents...")
        try:
            self.router = ContentRouter(self.llm)
            self.planner = ContentPlanner(self.llm)
            self.writer = ContentWriter(self.llm)
            self.quality_checker = QualityChecker(self.llm)
            self.logger.info("✅ All agents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise

        # Initialize memory systems
        self.logger.info("Initializing memory systems...")
        try:
            # self.brand_guidelines = BrandGuidelines()
            self.content_history = ContentHistory()
            self.user_preferences = UserPreferences()
            self.logger.info("✅ Memory systems initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize memory systems: {e}")
            raise

        self.logger.info("🎉 Content Pipeline initialization completed successfully")

    def process_request(self, request: ContentRequest) -> Dict[str, Any]:
        """Main pipeline to process content request"""
        start_time = time.time()
        request_id = request.request_id

        try:
            # Log pipeline start
            log_pipeline_start(request_id, request.topic, request.content_type)
            self.logger.info(
                f"Starting content processing pipeline for request: {request_id}"
            )

            # Step 1: Route the request
            log_pipeline_step("Routing Request", request_id, f"Topic: {request.topic}")
            log_agent_action(
                "Router",
                "Route Request",
                request_id,
                f"Content Type: {request.content_type}",
            )

            routing_start = time.time()
            routing_decision = self.router.route_request(request)
            routing_time = time.time() - routing_start
            log_performance("Request Routing", routing_time, request_id)

            self.logger.info(f"Routing completed: {routing_decision}")

            # Step 2: Create content plan
            log_pipeline_step(
                "Creating Content Plan",
                request_id,
                f"Target Audience: {request.target_audience}",
            )
            log_agent_action(
                "Planner",
                "Create Plan",
                request_id,
                f"Key Points: {len(request.key_points or [])}",
            )

            planning_start = time.time()
            plan = self.planner.create_plan(request)
            planning_time = time.time() - planning_start
            log_performance("Content Planning", planning_time, request_id)

            self.logger.info(f"Content plan created: {plan.title}")

            # Step 3: Write content
            log_pipeline_step(
                "Writing Content", request_id, f"Target Words: {plan.word_count_target}"
            )
            log_agent_action(
                "Writer", "Write Content", request_id, f"Tone: {plan.tone}"
            )

            writing_start = time.time()
            draft = self.writer.write_content(plan)
            writing_time = time.time() - writing_start
            log_performance("Content Writing", writing_time, request_id)

            self.logger.info(f"Content written: {draft.word_count} words")

            # Step 4: Quality check
            log_pipeline_step(
                "Quality Check", request_id, f"Word Count: {draft.word_count}"
            )
            log_agent_action(
                "Quality Checker",
                "Check Quality",
                request_id,
                f"Readability: {draft.readability_score}",
            )

            quality_start = time.time()
            quality_report = self.quality_checker.check_quality(draft)
            quality_time = time.time() - quality_start
            log_performance("Quality Check", quality_time, request_id)

            self.logger.info(
                f"Quality check completed: Score {quality_report.overall_score}"
            )

            # Step 5: Save to history
            log_pipeline_step(
                "Saving to History", request_id, f"Approved: {quality_report.approved}"
            )

            history_start = time.time()
            self.content_history.save_content_session(
                request, draft, quality_report, approved=quality_report.approved
            )
            history_time = time.time() - history_start
            log_performance("History Save", history_time, request_id)

            # Log pipeline completion
            total_time = time.time() - start_time
            log_pipeline_complete(request_id, True, quality_report.overall_score)
            log_performance(
                "Total Pipeline",
                total_time,
                request_id,
                f"Quality: {quality_report.overall_score}, Words: {draft.word_count}",
            )

            self.logger.info(
                f"✅ Pipeline completed successfully for {request_id} in {total_time:.2f}s"
            )

            return {
                "success": True,
                "request_id": draft.request_id,
                "routing_decision": routing_decision,
                "plan": plan.model_dump(),
                "draft": draft.model_dump(),
                "quality_report": quality_report.model_dump(),
                "requires_human_review": not quality_report.approved,
                "timestamp": datetime.now().isoformat(),
                "processing_time": total_time,
            }

        except Exception as e:
            total_time = time.time() - start_time
            log_pipeline_complete(request_id, False)
            log_error(
                "pipeline", e, request_id, f"Processing failed after {total_time:.2f}s"
            )
            self.logger.error(
                f"❌ Pipeline failed for {request_id}: {e}", exc_info=True
            )

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time": total_time,
            }

    def process_feedback(
        self, request_id: str, feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process human feedback on content"""
        start_time = time.time()

        try:
            self.logger.info(f"Processing feedback for request: {request_id}")
            self.logger.info(
                f"Feedback details: approved={feedback.get('approved')}, rating={feedback.get('quality_rating')}"
            )

            # Save feedback to history
            self.content_history.add_feedback(request_id, feedback)
            self.logger.info(f"Feedback saved to history for: {request_id}")

            # Learn from feedback
            if feedback.get("approved", False):
                self.logger.info(f"Learning from approved content: {request_id}")
                # Update user preferences based on successful content
                self.user_preferences.learn_from_feedback(
                    feedback.get("content_type", ""), feedback
                )
                self.logger.info(
                    f"User preferences updated from feedback: {request_id}"
                )
            else:
                self.logger.info(
                    f"Content not approved, analyzing feedback for improvements: {request_id}"
                )

            processing_time = time.time() - start_time
            self.logger.info(
                f"✅ Feedback processing completed for {request_id} in {processing_time:.2f}s"
            )

            return {
                "success": True,
                "message": "Feedback processed and learned from",
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            log_error(
                "pipeline",
                e,
                request_id,
                f"Feedback processing failed after {processing_time:.2f}s",
            )
            self.logger.error(
                f"❌ Feedback processing failed for {request_id}: {e}", exc_info=True
            )

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

    def get_content_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of content request"""
        try:
            self.logger.info(f"Retrieving status for request: {request_id}")

            for session in self.content_history.history:
                if session["draft"]["request_id"] == request_id:
                    status = (
                        "approved"
                        if session.get("approved", False)
                        else "pending_review"
                    )

                    self.logger.info(
                        f"Status found for {request_id}: {status} (Quality: {session['quality_report']['overall_score']})"
                    )

                    return {
                        "found": True,
                        "status": status,
                        "quality_score": session["quality_report"]["overall_score"],
                        "feedback": session.get("feedback"),
                        "created_at": session["timestamp"],
                    }

            self.logger.warning(f"Status not found for request: {request_id}")
            return {"found": False}

        except Exception as e:
            log_error("pipeline", e, request_id, "Status retrieval failed")
            self.logger.error(
                f"❌ Error retrieving status for {request_id}: {e}", exc_info=True
            )
            return {"found": False, "error": str(e)}
