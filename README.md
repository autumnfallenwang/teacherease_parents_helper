# TeacherEase Parents Helper

**Version 1.0.0**

Automated grade monitoring and email reporting system for TeacherEase parent portal. Scrapes student grades, identifies areas needing attention, and sends formatted HTML email reports.

## Features

- 🤖 **Automated Scraping**: Headless browser automation using Playwright
- 📧 **Email Reports**: Color-coded HTML emails with detailed breakdowns
- ⚠️ **Smart Alerts**: Highlights missing assignments, low scores, and below-meeting standards
- 🕐 **Scheduled Execution**: Daily cron job for hands-free monitoring
- 🔒 **Secure**: All credentials stored in `.env` file (not committed to repo)
- 🎨 **Rich Formatting**: Professional HTML emails with tables and color coding

## Email Report Includes

- **Summary**: Total classes, meeting expectations, needs attention, missing assignments
- **Classes Needing Attention**: Detailed breakdown with assignments
- **Missing Assignments**: Highlighted with 🚨 indicator and red background
- **Low Scores**: Yellow highlighting for grades below Meeting (B, P grades)
- **Special Statuses**: Shows Excused, Handed In, and other status indicators
- **Classes Meeting Expectations**: Simple list of classes doing well

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Playwright (for browser automation)
- Gmail account with App Password (or other SMTP service)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/teacherease_parents_helper.git
   cd teacherease_parents_helper
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Install Playwright browsers**
   ```bash
   uv run playwright install chromium
   ```

## Configuration

1. **Copy the example environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials**
   ```bash
   # TeacherEase Login
   TEACHEREASE_USERNAME=your_student_email@school.org
   TEACHEREASE_PASSWORD=your_password

   # Student Information
   STUDENT_NAME=Your Child's Name
   STUDENT_SCHOOL=School Name
   STUDENT_GRADE=7

   # Email Configuration
   EMAIL_RECIPIENT=your_email@example.com
   EMAIL_FROM=sender_email@gmail.com
   EMAIL_PASSWORD=your_gmail_app_password
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587

   # Scraper Settings
   HEADLESS_BROWSER=true
   SAVE_DEBUG_HTML=true
   EMAIL_TEST_MODE=false
   ```

3. **Get Gmail App Password**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification
   - Generate App Password: [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password to `EMAIL_PASSWORD` in `.env`

## Usage

### Manual Run
```bash
uv run python main.py
```

### Automated Daily Runs

The project includes a shell script for cron automation:

1. **Make the script executable** (if not already)
   ```bash
   chmod +x run_daily.sh
   ```

2. **Set up cron job**
   ```bash
   crontab -e
   ```

3. **Add this line** (runs daily at 2:14 AM)
   ```bash
   14 2 * * * /path/to/teacherease_parents_helper/run_daily.sh >> /path/to/teacherease_parents_helper/logs/cron.log 2>&1
   ```

4. **Ensure cron service is running**
   ```bash
   sudo systemctl start cronie
   sudo systemctl enable cronie
   ```

### Test Mode

To save emails to a file instead of sending:
```bash
# In .env
EMAIL_TEST_MODE=true
```

Emails will be saved to `logs/email_report_YYYYMMDD_HHMMSS.html`

## Project Structure

```
teacherease_parents_helper/
├── main.py                 # Main entry point
├── run_daily.sh           # Shell script for cron
├── pyproject.toml         # Project dependencies
├── .env                   # Configuration (not in repo)
├── .env.example           # Configuration template
├── src/
│   ├── scraper.py         # Browser automation & scraping
│   ├── data_parser.py     # HTML parsing & data extraction
│   └── email_sender.py    # Email template & SMTP sending
└── logs/                  # Log files & email reports (not in repo)
```

## Troubleshooting

### Cron job not running
- Check if cron service is active: `systemctl status cronie`
- Check cron logs: `cat logs/cron.log`
- Verify script permissions: `ls -la run_daily.sh`

### Email not sending
- Verify Gmail App Password (not regular password)
- Check if 2-Step Verification is enabled
- Test with `EMAIL_TEST_MODE=true` first
- Check logs for error messages

### Browser issues
- Make sure Playwright is installed: `uv run playwright install chromium`
- Check if running in headless mode: `HEADLESS_BROWSER=true`
- For debugging, set `HEADLESS_BROWSER=false` to see browser

### Login failures
- Verify TeacherEase credentials
- Check if TeacherEase website has changed
- Look at saved HTML in `logs/` for debugging

## Security Notes

- ✅ Never commit `.env` file to repository
- ✅ Use App Passwords, not main passwords
- ✅ Keep `logs/` folder private (contains student data)
- ✅ Review `.gitignore` before pushing changes
- ⚠️ Limit access to server running the script
- ⚠️ Regularly rotate passwords and app passwords

## Contributing

This is a personal project, but feel free to fork and adapt for your own use!

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Jinja2](https://jinja.palletsprojects.com/) - Email templating
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

---

**Version 1.0.0** - Initial release with full automation support
