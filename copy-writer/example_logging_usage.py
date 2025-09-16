"""
Example usage of the logging system in the Content Writer Agent project.
This demonstrates how to use the centralized logging configuration.
"""

import os
from config.logging_config import (
    get_logger,
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_step,
    log_pipeline_complete,
    log_agent_action,
    log_performance,
    log_error,
)


def main():
    """Example of how to use the logging system"""

    # Get a logger for this module
    logger = get_logger(__name__)

    # Get the pipeline logger for structured logging
    pipeline_logger = get_pipeline_logger()

    # Example 1: Basic logging
    logger.info("🚀 Starting Content Writer Agent example")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")

    # Example 2: Pipeline logging
    request_id = "example-123"
    log_pipeline_start(request_id, "Example Topic", "blog_post")

    # Example 3: Agent action logging
    log_agent_action("ContentPlanner", "Create Plan", request_id, "Topic: Example")

    # Example 4: Performance logging
    import time

    start_time = time.time()
    time.sleep(0.1)  # Simulate some work
    duration = time.time() - start_time
    log_performance("Example Operation", duration, request_id, "Simulated work")

    # Example 5: Pipeline step logging
    log_pipeline_step("Content Planning", request_id, "Creating outline")
    log_pipeline_step("Content Writing", request_id, "Generating content")

    # Example 6: Error logging
    try:
        # Simulate an error
        raise ValueError("This is an example error")
    except Exception as e:
        log_error("example", e, request_id, "Simulated error for demonstration")

    # Example 7: Pipeline completion
    log_pipeline_complete(request_id, True, 85.5)

    logger.info("✅ Example completed successfully")

    # Example 8: Different log levels
    logger.debug("Debug: Detailed information for debugging")
    logger.info("Info: General information about program execution")
    logger.warning("Warning: Something unexpected happened")
    logger.error("Error: A serious problem occurred")
    logger.critical("Critical: A very serious error occurred")


if __name__ == "__main__":
    # Set environment variables for logging configuration
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_DIR"] = "logs"
    os.environ["ENABLE_CONSOLE_LOGGING"] = "true"
    os.environ["ENABLE_FILE_LOGGING"] = "true"

    main()
