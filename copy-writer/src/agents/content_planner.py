from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..models.content_models import ContentRequest, ContentPlan
from ..tools.seo_tools import SEOAnalyzer
from typing import List
import uuid
import time
from config.logging_config import get_logger, log_agent_action, log_performance


class ContentPlanner:
    def __init__(self, llm: ChatOpenAI):
        self.logger = get_logger(__name__)
        self.llm = llm
        self.seo_analyzer = SEOAnalyzer()
        self.logger.info("Content Planner agent initialized")
        self.planning_prompt = PromptTemplate(
            template="""
            You are an expert content strategist. Create a detailed content plan based on this request.
            
            CONTENT REQUEST:
            Topic: {topic}
            Content Type: {content_type}
            Target Audience: {target_audience}
            Tone: {tone}
            Length: {length}
            SEO Keywords: {seo_keywords}
            Key Points: {key_points}
            Brand Voice: {brand_voice}
            
            Create a comprehensive content plan with:
            1. A compelling, SEO-optimized title
            2. Detailed outline (5-8 main points)
            3. Target keywords to include
            4. Key messages to convey
            5. Word count target
            
            Format your response as:
            TITLE: [compelling title]
            OUTLINE:
            1. [Main point 1]
            2. [Main point 2]
            ...
            
            TARGET_KEYWORDS: [keyword1, keyword2, ...]
            KEY_MESSAGES: [message1, message2, ...]
            WORD_COUNT_TARGET: [number]
            TONE_NOTES: [specific tone guidance]
            """,
            input_variables=[
                "topic",
                "content_type",
                "target_audience",
                "tone",
                "length",
                "seo_keywords",
                "key_points",
                "brand_voice",
            ],
        )

    def create_plan(self, request: ContentRequest) -> ContentPlan:
        """Create detailed content plan from request"""
        start_time = time.time()

        try:
            self.logger.info(f"Creating content plan for topic: {request.topic}")
            log_agent_action(
                "ContentPlanner",
                "Create Plan",
                request.request_id,
                f"Topic: {request.topic}",
            )

            # Enhance keywords with SEO research if needed
            self.logger.debug("Enhancing keywords with SEO research")
            keyword_start = time.time()
            enhanced_keywords = self._enhance_keywords(
                request.topic, request.seo_keywords or []
            )
            keyword_time = time.time() - keyword_start
            log_performance("Keyword Enhancement", keyword_time, request.request_id)

            self.logger.info(f"Enhanced keywords: {enhanced_keywords}")

            # Generate plan using LLM
            self.logger.info("Generating content plan with LLM...")
            prompt = self.planning_prompt.format(
                topic=request.topic,
                content_type=request.content_type.value,
                target_audience=request.target_audience or "general audience",
                tone=request.tone or "professional",
                length=request.length or "medium",
                seo_keywords=", ".join(enhanced_keywords),
                key_points=", ".join(request.key_points or []),
                brand_voice=request.brand_voice or "authentic and helpful",
            )

            llm_start = time.time()
            response = self.llm.invoke(prompt)
            llm_time = time.time() - llm_start
            log_performance("LLM Plan Generation", llm_time, request.request_id)

            self.logger.info("LLM response received, parsing plan data...")
            plan_data = self._parse_plan_response(response.content)

            # Create ContentPlan object
            plan = ContentPlan(
                request_id=str(uuid.uuid4()),
                title=plan_data.get("title", f"Content about {request.topic}"),
                outline=plan_data.get("outline", []),
                target_keywords=enhanced_keywords,
                word_count_target=plan_data.get("word_count_target", 800),
                tone=plan_data.get("tone_notes", request.tone or "professional"),
                key_messages=plan_data.get("key_messages", []),
                research_notes={"seo_analysis": "completed"},
            )

            total_time = time.time() - start_time
            log_performance(
                "Content Planning",
                total_time,
                request.request_id,
                f"Outline points: {len(plan.outline)}",
            )
            self.logger.info(
                f"✅ Content plan created for {request.request_id} in {total_time:.2f}s: {plan.title}"
            )

            return plan

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"❌ Content planning failed for {request.request_id} after {total_time:.2f}s: {e}",
                exc_info=True,
            )
            raise

    def _enhance_keywords(self, topic: str, existing_keywords: List[str]) -> List[str]:
        """Enhance keyword list with SEO research"""
        self.logger.debug(f"Enhancing keywords for topic: {topic}")

        if not existing_keywords:
            # Extract keywords from topic if none provided
            self.logger.debug("No existing keywords provided, extracting from topic")
            suggested_keywords = self.seo_analyzer.extract_keywords(topic)
            result = suggested_keywords[:5]  # Top 5 keywords
            self.logger.debug(f"Extracted {len(result)} keywords from topic")
            return result

        self.logger.debug(f"Using {len(existing_keywords)} existing keywords")
        return existing_keywords

    def _parse_plan_response(self, response: str) -> dict:
        """Parse LLM planning response into structured format"""
        plan_data = {}
        current_section = None
        outline_points = []

        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("TITLE:"):
                plan_data["title"] = line.replace("TITLE:", "").strip()
            elif line.startswith("OUTLINE:"):
                current_section = "outline"
            elif line.startswith("TARGET_KEYWORDS:"):
                keywords = line.replace("TARGET_KEYWORDS:", "").strip()
                plan_data["target_keywords"] = [k.strip() for k in keywords.split(",")]
            elif line.startswith("KEY_MESSAGES:"):
                messages = line.replace("KEY_MESSAGES:", "").strip()
                plan_data["key_messages"] = [m.strip() for m in messages.split(",")]
            elif line.startswith("WORD_COUNT_TARGET:"):
                count = line.replace("WORD_COUNT_TARGET:", "").strip()
                # Parse word count range (e.g. "800-1000") into average target
                count_parts = count.split("-")
                if len(count_parts) == 2:
                    min_count = int(
                        "".join(filter(str.isdigit, count_parts[0])) or "800"
                    )
                    max_count = int(
                        "".join(filter(str.isdigit, count_parts[1])) or "1000"
                    )
                    plan_data["word_count_target"] = (min_count + max_count) // 2
                else:
                    # If no range provided, use single number or default to 800
                    plan_data["word_count_target"] = int(
                        "".join(filter(str.isdigit, count)) or "800"
                    )
            elif line.startswith("TONE_NOTES:"):
                plan_data["tone_notes"] = line.replace("TONE_NOTES:", "").strip()
            elif current_section == "outline" and (
                line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."))
            ):
                point = line.split(".", 1)[1].strip()
                outline_points.append(point)

        if outline_points:
            plan_data["outline"] = outline_points

        return plan_data


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from src.models.content_models import ContentRequest, ContentType, Priority

    load_dotenv()

    llm_config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("OPENAI_MODEL"),
    }
    planner = ContentPlanner(llm=ChatOpenAI(**llm_config))

    request = ContentRequest(
        topic="iPhone 17 Air 512GB Color - Lavender",
        content_type=ContentType.PRODUCT_DESCRIPTION,
        priority=Priority.MEDIUM,
        target_audience="early adopters and tech enthusiasts",
        tone="premium and aspirational",
        length="medium",
    )
    plan = planner.create_plan(request)
    print(plan)
