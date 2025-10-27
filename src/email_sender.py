"""
Email sender for TeacherEase grade reports
Supports both real SMTP and test mode (save to file)
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EmailSender:
    """Send or save email reports"""
    
    def __init__(self, test_mode=True):
        self.test_mode = test_mode
        self.config = self._load_config()
    
    def _load_config(self):
        """Load email configuration from environment"""
        return {
            'recipient': os.getenv('EMAIL_RECIPIENT', 'test@example.com'),
            'from_email': os.getenv('EMAIL_FROM', 'sender@example.com'),
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'password': os.getenv('EMAIL_PASSWORD', ''),
        }
    
    def create_email_html(self, data: dict) -> str:
        """
        Generate HTML email from grade data
        """
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .summary-item { display: inline-block; margin: 10px 20px 10px 0; }
        .critical { background: #e74c3c; color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .critical h2 { color: white; }
        .warning { background: #f39c12; color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .warning h2 { color: white; }
        .success { background: #27ae60; color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .success h2 { color: white; }
        .class-list { list-style: none; padding: 0; }
        .class-item { padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; background: #f8f9fa; color: #333; }
        .missing-item { padding: 10px; margin: 5px 0; border-left: 4px solid #e74c3c; background: #ffe6e6; color: #333; }
        .standard { padding: 8px; margin: 5px 0; background: #fff3cd; border-left: 4px solid #ffc107; color: #333; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #34495e; color: white; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 2px solid #bdc3c7; color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 TeacherEase Grade Report - {{ student_name }}</h1>
        <p><strong>Report Date:</strong> {{ report_date }}</p>
        
        <div class="summary">
            <h3>📈 Summary</h3>
            <div class="summary-item"><strong>Total Classes:</strong> {{ total_classes }}</div>
            <div class="summary-item"><strong>Meeting Expectations:</strong> {{ meeting_count }}</div>
            <div class="summary-item"><strong>Needs Attention:</strong> {{ needs_attention_count }}</div>
            <div class="summary-item"><strong>Missing Assignments:</strong> {{ missing_count }}</div>
        </div>
        
        {% if missing_work %}
        <div class="critical">
            <h2>🚨 Missing Assignments ({{ missing_work|length }})</h2>
            {% for item in missing_work %}
            <div class="missing-item">
                <strong>{{ item.assignment }}</strong><br>
                Class: {{ item.class }}<br>
                Due: {{ item.due_date }}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if classes_needing_attention %}
        <div class="warning">
            <h2>⚠️ Classes Needing Attention</h2>
            {% for cls in classes_needing_attention %}
            <div class="class-item">
                <strong>{{ cls.name }}</strong> - {{ cls.status }}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if detailed_classes %}
        <h2>📚 Detailed Class Information</h2>
        {% for cls in detailed_classes %}
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
            <h3 style="color: #e74c3c;">{{ cls.class_name }}</h3>
            {% if cls.summary.missing_assignments > 0 %}
            <p style="color: #e74c3c;"><strong>⚠️ Missing Assignments:</strong> {{ cls.summary.missing_assignments }}</p>
            {% endif %}

            {% if cls.standards %}
            {% for std in cls.standards %}
            {% if not std.is_meeting or std.missing_count > 0 or std.low_score_count > 0 %}
            <div style="margin: 15px 0; padding: 12px; border-left: 4px solid #e67e22; background: white;">
                <div style="margin-bottom: 8px;">
                    <strong style="font-size: 16px;">{{ std.name }}</strong>
                    <span style="float: right; font-weight: bold; color: {% if std.score_numeric < 2 %}#e74c3c{% else %}#f39c12{% endif %};">
                        {{ std.score }}
                    </span>
                </div>

                {% if std.children %}
                <div style="margin-left: 15px;">
                    {% for child in std.children %}
                    {% if not child.is_meeting or child.missing_count > 0 or child.low_score_count > 0 %}
                    <div style="margin: 10px 0; padding: 8px; background: #fff3cd; border-left: 3px solid #ffc107;">
                        <strong>{{ child.name }}</strong>: <span style="font-weight: bold;">{{ child.score }}</span>

                        {% if child.assignments %}
                        <div style="margin-top: 8px; font-size: 13px;">
                            <table style="width: 100%; font-size: 12px; margin-top: 5px;">
                                <tr style="background: #f5f5f5;">
                                    <th>Assignment</th>
                                    <th>Due</th>
                                    <th>Grade</th>
                                </tr>
                                {% for asn in child.assignments %}
                                {% if asn.is_missing or (asn.grade_numeric < 3.0 and asn.grade_numeric > 0) or asn.grade in ['Excused', 'Handed In', ''] %}
                                <tr{% if asn.is_missing %} style="background: #ffe6e6;"{% elif asn.grade_numeric > 0 and asn.grade_numeric < 2 %} style="background: #fff3cd;"{% endif %}>
                                    <td>{{ asn.name }}</td>
                                    <td>{{ asn.due_date }}</td>
                                    <td><strong{% if asn.is_missing %} style="color: #e74c3c;"{% elif asn.grade_numeric > 0 and asn.grade_numeric < 2 %} style="color: #f39c12;"{% elif asn.grade in ['Excused', 'Handed In'] %} style="color: #7f8c8d;"{% endif %}>
                                        {{ asn.grade if asn.grade else 'Not Graded' }}{% if asn.is_missing %} 🚨{% endif %}
                                    </strong></td>
                                </tr>
                                {% endif %}
                                {% endfor %}
                            </table>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
                {% endif %}

                {% if std.assignments %}
                <div style="margin-top: 8px;">
                    <table style="width: 100%; font-size: 12px;">
                        <tr style="background: #f5f5f5;">
                            <th>Assignment</th>
                            <th>Due</th>
                            <th>Grade</th>
                        </tr>
                        {% for asn in std.assignments %}
                        {% if asn.is_missing or (asn.grade_numeric < 3.0 and asn.grade_numeric > 0) or asn.grade in ['Excused', 'Handed In', ''] %}
                        <tr{% if asn.is_missing %} style="background: #ffe6e6;"{% elif asn.grade_numeric > 0 and asn.grade_numeric < 2 %} style="background: #fff3cd;"{% endif %}>
                            <td>{{ asn.name }}</td>
                            <td>{{ asn.due_date }}</td>
                            <td><strong{% if asn.is_missing %} style="color: #e74c3c;"{% elif asn.grade_numeric > 0 and asn.grade_numeric < 2 %} style="color: #f39c12;"{% elif asn.grade in ['Excused', 'Handed In'] %} style="color: #7f8c8d;"{% endif %}>
                                {{ asn.grade if asn.grade else 'Not Graded' }}{% if asn.is_missing %} 🚨{% endif %}
                            </strong></td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </table>
                </div>
                {% endif %}
            </div>
            {% endif %}
            {% endfor %}
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}
        
        {% if classes_meeting %}
        <div class="success">
            <h2>✅ Classes Meeting Expectations</h2>
            <ul class="class-list">
            {% for cls in classes_meeting %}
                <li class="class-item">{{ cls.name }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>🤖 Generated automatically by TeacherEase Parents Helper</p>
            <p>This report was generated on {{ report_date }}</p>
        </div>
    </div>
</body>
</html>
        """)
        
        # Prepare template data
        overview = data.get('overview', {})
        summary = overview.get('summary', {})
        
        # Get list of classes we scraped in detail
        detailed_class_names = {cls['class_name'] for cls in data.get('detailed_classes', [])}

        # Classes needing attention are those we scraped in detail
        classes_needing_attention = [c for c in overview.get('classes', []) if c.get('name') in detailed_class_names]

        # All other classes go in "meeting expectations" section
        classes_meeting = [c for c in overview.get('classes', []) if c.get('name') not in detailed_class_names]

        # Calculate total missing assignments from detailed classes
        total_missing = sum(cls.get('summary', {}).get('missing_assignments', 0) for cls in data.get('detailed_classes', []))

        template_data = {
            'student_name': data.get('student_name', 'Student'),
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_classes': summary.get('total_classes', 0),
            'meeting_count': len(classes_meeting),
            'needs_attention_count': len(classes_needing_attention),
            'missing_count': total_missing,
            'missing_work': overview.get('missing_work', []),
            'classes_needing_attention': classes_needing_attention,
            'classes_meeting': classes_meeting,
            'detailed_classes': data.get('detailed_classes', [])
        }
        
        return template.render(**template_data)
    
    def send_email(self, subject: str, html_content: str) -> bool:
        """
        Send email via SMTP or save to file in test mode
        """
        if self.test_mode:
            return self._save_email_to_file(subject, html_content)
        else:
            return self._send_via_smtp(subject, html_content)
    
    def _save_email_to_file(self, subject: str, html_content: str) -> bool:
        """Save email to file for testing"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"email_report_{timestamp}.html"
            filepath = Path(__file__).parent.parent / 'logs' / filename
            
            filepath.write_text(html_content, encoding='utf-8')
            
            logger.info(f"✅ Email saved to: {filepath}")
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📬 To: {self.config['recipient']}")
            
            print(f"\n{'='*60}")
            print(f"📧 EMAIL SAVED TO FILE (Test Mode)")
            print(f"{'='*60}")
            print(f"Subject: {subject}")
            print(f"To: {self.config['recipient']}")
            print(f"File: {filepath}")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save email: {e}")
            return False
    
    def _send_via_smtp(self, subject: str, html_content: str) -> bool:
        """Send email via SMTP (real sending)"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['from_email']
            msg['To'] = self.config['recipient']
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['from_email'], self.config['password'])
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {self.config['recipient']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_grade_report(self, data: dict) -> bool:
        """
        Generate and send grade report from scraped data
        """
        subject = f"📊 TeacherEase Update: {data.get('student_name', 'Student')} - {datetime.now().strftime('%Y-%m-%d')}"
        html_content = self.create_email_html(data)
        
        return self.send_email(subject, html_content)


if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        'student_name': 'Test Student',
        'overview': {
            'classes': [
                {'name': 'Mathematics 7', 'status': 'Meeting', 'needs_attention': False},
                {'name': 'French 7', 'status': 'Click on Details', 'needs_attention': True},
            ],
            'missing_work': [
                {'due_date': '9/11/2025', 'class': 'French 7', 'assignment': 'Gimkit - avoir'}
            ],
            'summary': {
                'total_classes': 2,
                'meeting_expectations': 1,
                'needs_attention': 1,
                'missing_count': 1
            }
        },
        'detailed_classes': []
    }
    
    sender = EmailSender(test_mode=True)
    sender.send_grade_report(sample_data)
