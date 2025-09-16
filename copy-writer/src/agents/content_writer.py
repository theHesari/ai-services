from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..models.content_models import ContentPlan, ContentDraft
from ..memory.brand_guidelines import BrandGuidelines
from ..tools.content_tools import ContentTools
import uuid
import time
from config.logging_config import get_logger, log_agent_action, log_performance


class ContentWriter:
    def __init__(self, llm: ChatOpenAI):
        self.logger = get_logger(__name__)
        self.llm = llm
        self.brand_guidelines = BrandGuidelines()
        self.content_tools = ContentTools()
        self.logger.info("Content Writer agent initialized")

        self.writing_prompt = PromptTemplate(
            template="""
            You are an expert content writer. Write engaging, high-quality content based on this plan.
            
            CONTENT PLAN:
            Title: {title}
            Target Keywords: {target_keywords}
            Word Count Target: {word_count_target}
            Tone: {tone}
            
            OUTLINE TO FOLLOW:
            {outline}
            
            KEY MESSAGES TO INCLUDE:
            {key_messages}
            
            BRAND GUIDELINES:
            {brand_guidelines}
            
            WRITING INSTRUCTIONS:
            - Write compelling, engaging content that follows the outline
            - Naturally incorporate the target keywords (don't stuff them)
            - Maintain consistent tone throughout
            - Use clear, scannable formatting with headers and bullet points where appropriate
            - Include a strong introduction and conclusion
            - Make it valuable and actionable for the reader
            - Target approximately {word_count_target} words
            
            Write the complete content now:
            """,
            input_variables=[
                "title",
                "target_keywords",
                "word_count_target",
                "tone",
                "outline",
                "key_messages",
                "brand_guidelines",
            ],
        )

    def write_content(
        self, plan: ContentPlan, brand_context: str = None
    ) -> ContentDraft:
        """Write content based on the provided plan"""
        start_time = time.time()

        try:
            self.logger.info(f"Starting content writing for plan: {plan.title}")
            log_agent_action(
                "ContentWriter",
                "Write Content",
                plan.request_id,
                f"Title: {plan.title}",
            )

            # Get brand guidelines
            guidelines = brand_context or self.brand_guidelines.get_guidelines()
            self.logger.debug("Retrieved brand guidelines")

            # Format outline for prompt
            outline_text = "\n".join(
                [f"{i+1}. {point}" for i, point in enumerate(plan.outline)]
            )
            self.logger.debug(f"Formatted outline with {len(plan.outline)} points")

            # Generate content
            self.logger.info("Generating content with LLM...")
            prompt = self.writing_prompt.format(
                title=plan.title,
                target_keywords=", ".join(plan.target_keywords),
                word_count_target=plan.word_count_target,
                tone=plan.tone,
                outline=outline_text,
                key_messages="\n".join([f"- {msg}" for msg in plan.key_messages]),
                brand_guidelines=guidelines,
            )

            llm_start = time.time()
            response = self.llm.invoke(prompt)
            llm_time = time.time() - llm_start
            log_performance("LLM Content Generation", llm_time, plan.request_id)

            content = response.content.strip()
            self.logger.info(
                f"Content generated successfully: {len(content)} characters"
            )

            # Calculate word count
            word_count = len(content.split())
            self.logger.info(f"Content word count: {word_count}")

            # Generate meta description
            meta_description = self._generate_meta_description(plan.title, content)
            self.logger.debug("Generated meta description")

            # Extract/suggest tags
            tags = self._extract_tags(content, plan.target_keywords)
            self.logger.debug(f"Extracted {len(tags)} tags")

            # Calculate readability
            readability_start = time.time()
            readability_score = self.content_tools.calculate_readability(content)
            readability_time = time.time() - readability_start
            log_performance(
                "Readability Calculation", readability_time, plan.request_id
            )

            self.logger.info(f"Readability score: {readability_score}")

            # Create draft
            draft = ContentDraft(
                request_id=plan.request_id,
                title=plan.title,
                content=content,
                meta_description=meta_description,
                tags=tags,
                word_count=word_count,
                readability_score=readability_score,
            )

            total_time = time.time() - start_time
            log_performance(
                "Content Writing",
                total_time,
                plan.request_id,
                f"Words: {word_count}, Readability: {readability_score}",
            )
            self.logger.info(
                f"✅ Content writing completed for {plan.request_id} in {total_time:.2f}s"
            )

            return draft

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"❌ Content writing failed for {plan.request_id} after {total_time:.2f}s: {e}",
                exc_info=True,
            )
            raise

    def _generate_meta_description(self, title: str, content: str) -> str:
        """Generate SEO meta description"""
        self.logger.debug("Generating meta description")

        # Simple extraction of first meaningful sentence or paragraph
        sentences = content.split(".")[:3]  # First 3 sentences
        meta = ". ".join(sentences).strip()

        # Ensure it's within meta description limits (150-160 chars)
        if len(meta) > 155:
            meta = meta[:150] + "..."
            self.logger.debug("Meta description truncated to fit length limits")

        self.logger.debug(f"Generated meta description: {len(meta)} characters")
        return meta

    def _extract_tags(self, content: str, keywords: list) -> list:
        """Extract relevant tags from content and keywords"""
        self.logger.debug(f"Extracting tags from {len(keywords)} keywords")

        tags = []

        # Add keywords as tags
        tags.extend(keywords)

        # Could add more sophisticated tag extraction here
        # For now, just return keywords as tags

        unique_tags = list(set(tags))  # Remove duplicates
        self.logger.debug(f"Extracted {len(unique_tags)} unique tags")
        return unique_tags


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from src.models.content_models import ContentPlan

    load_dotenv()

    llm_config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("OPENAI_MODEL"),
    }

    writer = ContentWriter(llm=ChatOpenAI(**llm_config))

    plan = ContentPlan(
        request_id="123",
        title="iPhone 17 Air 512GB Color - Lavender",
        outline=["Outline 1", "Outline 2", "Outline 3"],
        target_keywords=["iPhone 17", "Air", "512GB", "Lavender"],
        word_count_target=800,
        tone="premium and aspirational",
        key_messages=["Key message 1", "Key message 2", "Key message 3"],
    )

    draft = writer.write_content(plan)
    print(draft)
