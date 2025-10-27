#!/usr/bin/env python3
"""
TeacherEase Parents Helper - Main Entry Point
Scrapes grade data and sends email reports
"""
import json
import logging
from pathlib import Path
import os
from src.scraper import TeacherEaseScraper
from src.email_sender import EmailSender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main workflow: scrape → parse → email"""
    logger.info("="*60)
    logger.info("🚀 TeacherEase Parents Helper Starting")
    logger.info("="*60)

    try:
        # Step 1: Scrape the data
        logger.info("📡 Step 1: Scraping TeacherEase...")
        scraper = TeacherEaseScraper()
        data = scraper.scrape_all_grades()

        logger.info("✅ Scraping complete!")
        logger.info(f"   - Total classes: {data['overview']['summary']['total_classes']}")
        logger.info(f"   - Classes needing attention: {data['overview']['summary']['needs_attention']}")
        logger.info(f"   - Detailed classes scraped: {len(data['detailed_classes'])}")

        # Print detailed classes info
        for cls in data['detailed_classes']:
            logger.info(f"   📚 {cls['class_name']}:")
            logger.info(f"      - Missing assignments: {cls['summary']['missing_assignments']}")

        # Step 2: Generate and send/save email
        logger.info("")
        logger.info("📧 Step 2: Generating email report...")
        email_test_mode = os.getenv('EMAIL_TEST_MODE', 'true').lower() == 'true'
        sender = EmailSender(test_mode=email_test_mode)
        success = sender.send_grade_report(data)

        if success:
            logger.info("✅ Email generated successfully!")
        else:
            logger.error("❌ Email generation failed")
            return 1

        logger.info("")
        logger.info("="*60)
        logger.info("🎉 Workflow complete!")
        logger.info("="*60)

        return 0

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
