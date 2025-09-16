from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..models.content_models import ContentRequest, ContentType, Priority
import time
from config.logging_config import get_logger, log_agent_action, log_performance


class ContentRouter:
    def __init__(self, llm: ChatOpenAI):
        self.logger = get_logger(__name__)
        self.llm = llm
        self.logger.info("Content Router agent initialized")
        self.routing_prompt = PromptTemplate(
            template="""
            You are a content routing agent. Analyze the incoming request and determine:
            1. Content type (if not specified)
            2. Complexity level (simple, moderate, complex)
            3. Required tools/research
            4. Estimated effort
            
            Request: {request_text}
            Current content type: {content_type}
            Priority: {priority}
            
            Provide routing decision in this format:
            CONTENT_TYPE: [confirmed type]
            COMPLEXITY: [simple/moderate/complex]
            TOOLS_NEEDED: [list of tools]
            ESTIMATED_TIME: [minutes]
            ROUTE_TO: [direct_write/full_pipeline]
            REASONING: [brief explanation]
            """,
            input_variables=["request_text", "content_type", "priority"],
        )

    def route_request(self, request: ContentRequest) -> Dict[str, Any]:
        """Route content request to appropriate workflow"""
        start_time = time.time()

        try:
            self.logger.info(f"Routing request for topic: {request.topic}")
            log_agent_action(
                "Router", "Route Request", request.request_id, f"Topic: {request.topic}"
            )

            # Create request text for analysis
            request_text = f"Topic: {request.topic}"
            if request.target_audience:
                request_text += f"\nAudience: {request.target_audience}"
            if request.key_points:
                request_text += f"\nKey points: {', '.join(request.key_points)}"
            if request.additional_context:
                request_text += f"\nContext: {request.additional_context}"

            self.logger.debug(f"Request text prepared: {len(request_text)} characters")

            # Get routing decision from LLM
            self.logger.info("Getting routing decision from LLM...")
            prompt = self.routing_prompt.format(
                request_text=request_text,
                content_type=request.content_type.value,
                priority=request.priority.value,
            )

            llm_start = time.time()
            response = self.llm.invoke(prompt)
            llm_time = time.time() - llm_start
            log_performance("LLM Routing Decision", llm_time, request.request_id)

            self.logger.info("LLM routing response received, parsing decision...")
            routing_decision = self._parse_routing_response(response.content)

            total_time = time.time() - start_time
            log_performance(
                "Request Routing",
                total_time,
                request.request_id,
                f"Route: {routing_decision.get('ROUTE_TO', 'unknown')}",
            )
            self.logger.info(
                f"✅ Request routed for {request.request_id} in {total_time:.2f}s: {routing_decision.get('ROUTE_TO', 'unknown')}"
            )

            return routing_decision

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"❌ Request routing failed for {request.request_id} after {total_time:.2f}s: {e}",
                exc_info=True,
            )
            raise

    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM routing response into structured format"""
        self.logger.debug("Parsing routing response from LLM")

        lines = response.strip().split("\n")
        decision = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key == "tools_needed":
                    decision[key] = [tool.strip() for tool in value.split(",")]
                elif key == "estimated_time":
                    decision[key] = int("".join(filter(str.isdigit, value)) or "30")
                else:
                    decision[key] = value

        return decision


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm_config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("OPENAI_MODEL"),
    }
    router = ContentRouter(llm=ChatOpenAI(**llm_config))

    request = ContentRequest(
        topic="iPhone 17 Air 512GB Color - Lavender",
        content_type=ContentType.PRODUCT_DESCRIPTION,
        priority=Priority.MEDIUM,
        target_audience="early adopters and tech enthusiasts",
        tone="premium and aspirational",
        length="medium",
    )

    router_decision = router.route_request(request)
    print(router_decision)
