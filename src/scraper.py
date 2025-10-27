"""
TeacherEase web scraper using Playwright
"""
import os
import logging
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
from .data_parser import GradeParser

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TeacherEaseScraper:
    """Scraper for TeacherEase grade and assignment data"""

    def __init__(self, headless=None):
        # Use .env setting if headless not specified
        if headless is None:
            headless = os.getenv('HEADLESS_BROWSER', 'true').lower() == 'true'

        self.headless = headless
        self.save_debug_html = os.getenv('SAVE_DEBUG_HTML', 'true').lower() == 'true'
        self.browser = None
        self.page = None
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from environment variables"""
        required_vars = ['TEACHEREASE_URL', 'TEACHEREASE_USERNAME', 'TEACHEREASE_PASSWORD']

        config = {}
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                raise ValueError(f"Missing required environment variable: {var}")
            config[var.lower().replace('teacherease_', '')] = value

        # Load optional settings
        config['student_name'] = os.getenv('STUDENT_NAME', 'Student')
        config['alert_threshold'] = int(os.getenv('ALERT_THRESHOLD', '2'))

        logger.info(f"Loaded configuration for {config['username']}")
        return config
    
    def start(self):
        """Start browser and create new page"""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        logger.info("Browser started successfully")
    
    def stop(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    def login(self):
        """Login to TeacherEase"""
        logger.info(f"Navigating to {self.config['url']}")
        self.page.goto(self.config['url'])

        # Click Log In link
        logger.info("Clicking Log In link...")
        self.page.click('text=Log In')
        self.page.wait_for_load_state('networkidle')

        # Fill login form - using placeholder selectors from PoC
        logger.info(f"Logging in as {self.config['username']}")
        self.page.fill('input[placeholder="Email Address"]', self.config['username'])
        self.page.fill('input[placeholder="Password"]', self.config['password'])
        
        # Click login button
        self.page.click('button:has-text("Log In")')
        self.page.wait_for_load_state('networkidle')
        
        # Verify login success
        if 'Student Main' in self.page.content():
            logger.info("Login successful!")
            return True
        else:
            logger.error("Login failed!")
            return False
    
    def navigate_to_grades(self):
        """Navigate to Grades page"""
        logger.info("Navigating to Grades page...")
        # Extract base URL and construct grades URL
        base_url = self.page.url.split('/parents')[0] if '/parents' in self.page.url else self.page.url.split('/App')[0]
        grades_url = base_url + '/App/Parents/StandardGrade/GradeViewAllWithProgress'
        logger.info(f"Grades URL: {grades_url}")
        self.page.goto(grades_url)
        self.page.wait_for_load_state('networkidle')
        logger.info(f"On page: {self.page.url}")
    
    def get_grades_overview(self):
        """Extract grades overview data"""
        logger.info("Extracting grades overview...")

        content = self.page.content()

        # Save HTML for debugging (optional)
        if self.save_debug_html:
            debug_html_path = Path(__file__).parent.parent / 'logs' / 'grades_page.html'
            debug_html_path.write_text(content, encoding='utf-8')
            logger.info(f"Saved HTML to {debug_html_path}")

        overview_data = GradeParser.parse_grades_overview(content)

        return overview_data

    def get_class_details(self, class_info: dict):
        """
        Navigate to class details page and extract detailed info
        Uses ClassID and CGPID from the overview data
        """
        class_name = class_info.get('name', 'Unknown')
        class_id = class_info.get('class_id')
        cgp_id = class_info.get('cgp_id')

        if not class_id or not cgp_id:
            logger.warning(f"Missing ClassID or CGPID for {class_name}")
            return None

        logger.info(f"Getting details for {class_name} (ClassID={class_id}, CGPID={cgp_id})...")

        try:
            # Construct the details URL
            # Use the common/ path that Chrome MCP showed works
            # Extract just the base domain
            from urllib.parse import urlparse
            parsed = urlparse(self.page.url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            details_url = f"{base_url}/common/StudentProgressStandardsDetails.aspx?ClassID={class_id}&CGPID={cgp_id}"

            logger.info(f"Navigating to: {details_url}")
            self.page.goto(details_url, timeout=60000)  # 60 second timeout
            self.page.wait_for_load_state('networkidle', timeout=30000)

            # Parse the class details page
            content = self.page.content()
            class_data = GradeParser.parse_class_details(content, class_name)

            # Save for debugging
            if self.save_debug_html:
                debug_path = Path(__file__).parent.parent / 'logs' / f'{class_name.replace(" ", "_").lower()}_details.html'
                debug_path.write_text(content, encoding='utf-8')
                logger.info(f"Saved details HTML to {debug_path}")

            return class_data

        except Exception as e:
            logger.error(f"Could not get details for {class_name}: {e}", exc_info=True)
            return None

    def scrape_all_grades(self):
        """Main scraping workflow"""
        try:
            self.start()

            if not self.login():
                raise Exception("Login failed")

            self.navigate_to_grades()
            overview = self.get_grades_overview()

            # Collect detailed data for classes that need attention
            detailed_classes = []
            for class_info in overview.get('classes', []):
                if class_info.get('needs_attention'):
                    details = self.get_class_details(class_info)
                    if details:
                        detailed_classes.append(details)

            # Combine all data
            result = {
                'overview': overview,
                'detailed_classes': detailed_classes,
                'student_name': self.config['student_name'],
                'alert_threshold': self.config['alert_threshold']
            }

            return result

        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            raise
        finally:
            self.stop()


if __name__ == "__main__":
    # headless parameter will be read from .env if not specified
    scraper = TeacherEaseScraper()
    data = scraper.scrape_all_grades()
    print("Scraping complete!")
    print(json.dumps(data, indent=2, default=str))
