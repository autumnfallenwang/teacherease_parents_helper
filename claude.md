# TeacherEase Parents Helper

## Project Overview
Automated monitoring system for parents to track their child's homework, grades, and assignments from TeacherEase. The system logs into TeacherEase, scrapes grade/assignment data, and sends email notifications highlighting areas of concern.

## Use Case
- **Parent User**: Wants to monitor child's academic progress on TeacherEase
- **Goal**: Receive automated email summaries showing:
  - Missing assignments
  - Grades below "Meeting" expectations (P=Progressing, B=Beginning, NY=Not Yet)
  - Standards not being met
  - Detailed breakdown by subject

## Student Information
- Configured via `.env` file (see `.env.example` for template)

## Tech Stack

### Core Application
- **Language**: Python 3
- **Web Automation**: Chrome DevTools Protocol (via MCP) for PoC, Playwright for production
  - Alternative: Selenium (fallback option)
- **Deployment**: Arch Linux (local development & initial deployment)
- **Scheduling**: cron job (initial), systemd timer (future)

### Email Service Options
1. **Gmail SMTP** (Current choice for simplicity)
   - Free for personal use
   - 500 emails/day limit
   - Requires app password with 2FA
   - Library: Python's `smtplib`

2. **Mailgun** (Future upgrade path)
   - 5,000 free emails/month
   - Better for service migration

3. **SendGrid** (Alternative)
   - 100 emails/day free tier

### Dependencies (Planned)
```
playwright>=1.40.0
python-dotenv>=1.0.0
jinja2>=3.1.2  # For email templates
requests>=2.31.0
beautifulsoup4>=4.12.0  # If needed for parsing
```

## Upgrade Path
1. **Phase 1** (Current): Local Python script + cron on Arch Linux
2. **Phase 2**: Docker containerization for portability
3. **Phase 3**: Deploy to cloud platform (AWS Lambda, Google Cloud Run, or DigitalOcean)
4. **Phase 4**: Switch to Mailgun/SendGrid for reliability

## TeacherEase Data Structure

### Grading Scale
- **M (Meeting)**: 3 points - ✅ Meeting expectations
- **P (Progressing)**: 2 points - ⚠️ NOT meeting (needs attention)
- **B (Beginning)**: 1 point - ⚠️⚠️ NOT meeting (critical)
- **NY (Not Yet)**: 0.5 points - ⚠️⚠️ NOT meeting (critical)

### Key Pages & Data Points

#### 1. Login Page
- URL: `https://www.teacherease.com/home.aspx`
- Fields: Email Address, Password
- Authentication: Standard form-based login

#### 2. Student Main Page
- Shows: Student name, school, grade, feed of recent activities
- Navigation: Quick links to Grades, Report Card, etc.

#### 3. Grades Overview Page
- URL Pattern: After clicking "Grades" from main menu
- Shows:
  - Class list with overall status (Meeting / Click on Details)
  - Missing Work section (Due date, Class, Assignment name)
  - Color-coded progress indicators

#### 4. Standards-Based Grades (Per Class)
- Accessed by: Clicking "Details" for each class
- Shows:
  - Standards with scores (e.g., "2.43=P", "3=M")
  - Standards categorized by skill area (Reading, Writing, Listening, Speaking, etc.)
  - Learning Habits scores by cycle
  - Calculation mode (e.g., "Decaying Weights")

#### 5. Grade Details (Assignment View)
- Accessed by: "View By Assignment" button
- Shows:
  - Due date
  - Assignment name (clickable for details)
  - Standards tested
  - Score with letter grade
  - Missing/Excused/Late indicators (with icons)

## Data Collected in PoC

### Example Classes Overview
- **Subject Area 1**: ✅ Meeting
- **Subject Area 2**: ⚠️ Issues found (example: missing assignments, low scores)
- **Subject Area 3**: ✅ Meeting

### Example Issues Detected
- Missing assignments with due dates
- Assignments scored below "Meeting" level (P, B, or NY)
- Standards not meeting expectations across multiple skill areas
- Learning habits tracking below target levels

## Project Structure (Planned)
```
teacherease_parents_helper/
├── claude.md                          # This file - project documentation
├── README.md                          # User-facing documentation
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore file
├── requirements.txt                   # Python dependencies
├── src/
│   ├── scraper.py                     # Main scraping logic
│   ├── email_sender.py                # Email formatting & sending
│   ├── data_parser.py                 # Parse TeacherEase data
│   └── config.py                      # Configuration management
├── templates/
│   └── email_template.html            # HTML email template
└── logs/
    └── scraper.log                    # Execution logs

# Ignored/Private files (not in repo):
├── .env                               # Actual environment variables (gitignored)
└── config/                            # Private config folder (gitignored)
    ├── credentials.txt                # TeacherEase login credentials
    └── email_config.txt               # Email settings
```

## Security Considerations
- ✅ Store credentials in `config/` folder (gitignored)
- ✅ Use `.env` for environment variables (gitignored)
- ✅ Never commit sensitive data to repository
- ✅ Use app passwords for email services (not main password)
- ⚠️ Consider encrypting credentials at rest
- ⚠️ Implement rate limiting to avoid account lockout

## Development Progress

### ✅ Phase 1: PoC & Exploration (COMPLETED)
- [x] Set up Chrome MCP for browser automation
- [x] Successfully login to TeacherEase
- [x] Navigate and map out grade pages
- [x] Identify data structure for missing assignments, low grades, standards
- [x] Document all findings
- [x] Create project documentation (claude.md)

### ✅ Phase 2: Python Script Development (COMPLETED)
- [x] Set up project structure with uv package manager
- [x] Create `.gitignore` and `.env.example` template
- [x] Install and configure Playwright for headless browser automation
- [x] Implement login automation with TeacherEase
- [x] Implement grade scraping logic for all classes
- [x] Parse and structure data (JSON processing)
- [x] Create HTML email template with Jinja2
- [x] Implement email sending (Gmail SMTP)
- [x] Add error handling and logging
- [x] Test end-to-end workflow successfully
- [x] Email reports with color-coded sections
- [x] Support for missing assignments, low scores, and special statuses (Excused, Handed In)

### ✅ Phase 3: Deployment & Automation (COMPLETED)
- [x] Create shell script for daily execution
- [x] Set up cron job for automated runs (2:14 AM daily)
- [x] Configure headless browser mode for server deployment
- [x] Set up logging to track execution
- [x] Test in production environment
- [x] Document setup instructions

### ⏳ Phase 4: Enhancements (FUTURE)
- [ ] Dockerize application
- [ ] Add configuration for multiple students
- [ ] Implement trend analysis (grade improvements/declines)
- [ ] Add web dashboard (optional)
- [ ] Migrate to cloud platform
- [ ] Switch to Mailgun/SendGrid

## Email Report Format (Planned)

### Subject Line
`📊 TeacherEase Update: [Student Name] - [Date]`

### Email Sections
1. **Executive Summary**
   - Overall status (e.g., "3 classes need attention")
   - Count of missing assignments
   - Count of below-standard grades

2. **🚨 Critical Issues**
   - Missing assignments (sorted by due date)
   - Grades at "Beginning" level (1=B)
   - Standards significantly below expectations

3. **⚠️ Areas Needing Attention**
   - "Progressing" grades (2=P)
   - Recent assignment scores below meeting

4. **✅ Classes Meeting Expectations**
   - Brief list of classes doing well

5. **📈 Recommendations**
   - Suggested focus areas
   - Upcoming assignments to watch

## Notes
- TeacherEase uses standards-based grading (not traditional A-F)
- "Meeting" (M=3) is the target - anything below needs attention
- Missing assignments are highlighted separately from low scores
- Some assignments may be "Excused" and don't count toward grades
- Grading uses "Decaying Weights" - recent assignments matter more

## Future Considerations
- Multi-child support for families with multiple students
- Comparison with previous grading periods
- Export data to CSV/JSON for external analysis
- Integration with calendar apps for due date reminders
- SMS notifications for critical issues (via Twilio)
