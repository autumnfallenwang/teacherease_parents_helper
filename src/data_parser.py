"""
Data parser for TeacherEase grade information
Extracts JSON data embedded in the grades page
"""
import json
import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class GradeParser:
    """Parse TeacherEase HTML to extract grade data"""

    # Status codes from TeacherEase
    STATUS_NOT_ASSESSED = 0  # No grades yet
    STATUS_MEETING = 1       # Meeting expectations
    STATUS_NEEDS_ATTENTION = 2  # Click on Details - not meeting

    @staticmethod
    def extract_json_data(html: str) -> List[Dict[str, Any]]:
        """
        Extract the JSON data embedded in the JavaScript on the grades page
        """
        # Find the JSON data in the kendoListView initialization
        # Pattern: "data":{"Data":[...classes array...]
        pattern = r'"data":\{"Data":\[(.*?)\],"Total"'
        
        match = re.search(pattern, html, re.DOTALL)
        
        if not match:
            logger.warning("Could not find JSON data in HTML")
            return []
        
        try:
            # Extract the array content
            json_str = '[' + match.group(1) + ']'
            
            # Parse the JSON
            classes_data = json.loads(json_str)
            
            logger.info(f"Successfully extracted JSON data for {len(classes_data)} classes")
            return classes_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return []

    @staticmethod
    def parse_grades_overview(html: str) -> Dict[str, Any]:
        """
        Parse the main grades overview page using the embedded JSON data
        """
        data = {
            'classes': [],
            'missing_work': [],
            'summary': {
                'total_classes': 0,
                'meeting_expectations': 0,
                'needs_attention': 0,
                'not_assessed': 0,
                'total_targets_meeting': 0,
                'total_targets_not_meeting': 0
            }
        }

        # Extract JSON data
        classes_json = GradeParser.extract_json_data(html)
        
        if not classes_json:
            logger.warning("No class data found")
            return data

        # Process each class
        for cls in classes_json:
            class_name = cls.get('ClassDescription', 'Unknown Class')
            instructor = cls.get('InstructorDescription', ['Unknown'])[0] if cls.get('InstructorDescription') else 'Unknown'
            
            grade_status = cls.get('GradeStatus', {})
            status_code = grade_status.get('Status', 0)
            
            progress = cls.get('Progress', {})
            targets_meeting = progress.get('LearningTargetsMeeting', 0)
            targets_not_meeting = progress.get('LearningTargetsNotMeeting', 0)
            
            # Determine status
            if status_code == GradeParser.STATUS_MEETING:
                status = 'Meeting'
                needs_attention = False
            elif status_code == GradeParser.STATUS_NEEDS_ATTENTION:
                status = 'Click on Details'
                needs_attention = True
            else:
                status = 'Not Assessed'
                needs_attention = False
            
            class_info = {
                'name': class_name,
                'instructor': instructor,
                'status': status,
                'status_code': status_code,
                'needs_attention': needs_attention,
                'targets_meeting': targets_meeting,
                'targets_not_meeting': targets_not_meeting,
                'total_targets': progress.get('TotalLeafLearningTargets', 0),
                'class_id': cls.get('ClassID'),
                'cgp_id': cls.get('CurrentCGPID')
            }
            
            data['classes'].append(class_info)
            data['summary']['total_classes'] += 1
            
            if status_code == GradeParser.STATUS_MEETING:
                data['summary']['meeting_expectations'] += 1
            elif status_code == GradeParser.STATUS_NEEDS_ATTENTION:
                data['summary']['needs_attention'] += 1
            else:
                data['summary']['not_assessed'] += 1
            
            data['summary']['total_targets_meeting'] += targets_meeting
            data['summary']['total_targets_not_meeting'] += targets_not_meeting

        # TODO: Parse missing work section (separate part of the page)
        # For now, we'll extract it from the HTML text
        data['missing_work'] = GradeParser._parse_missing_work(html)
        data['summary']['missing_count'] = len(data['missing_work'])

        logger.info(f"Parsed overview: {data['summary']['total_classes']} classes, "
                   f"{data['summary']['meeting_expectations']} meeting, "
                   f"{data['summary']['needs_attention']} need attention, "
                   f"{data['summary']['missing_count']} missing assignments")

        return data

    @staticmethod
    def _parse_missing_work(html: str) -> List[Dict[str, str]]:
        """Extract missing work from the HTML"""
        missing = []
        
        # Look for the missing work section
        # Pattern: date + time + class name + assignment name
        pattern = r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}\s+[AP]M)\s+([A-Z][^<\n]+?\d+)\s+([^<\n]+?)(?=\d{1,2}/\d{1,2}/\d{4}|$)'
        
        matches = re.finditer(pattern, html, re.MULTILINE)
        
        for match in matches:
            missing_item = {
                'due_date': f"{match.group(1)} {match.group(2)}",
                'class': match.group(3).strip(),
                'assignment': match.group(4).strip()
            }
            
            # Clean up assignment name
            assignment = missing_item['assignment'].split('\n')[0].strip()
            if len(assignment) > 0 and len(assignment) < 200:
                missing_item['assignment'] = assignment
                missing.append(missing_item)
        
        return missing

    @staticmethod
    def parse_class_details(html: str, class_name: str) -> Dict[str, Any]:
        """
        Parse detailed class grade page with standards and assignments
        Extracts standards hierarchy with scores and their associated assignments
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        result = {
            'class_name': class_name,
            'standards': [],
            'summary': {
                'missing_assignments': 0
            }
        }

        # Find all root-level standards
        root_standards = soup.find_all('ul', class_='root-standard-item')

        for root_std_ul in root_standards:
            # Each root UL contains LI elements - parse each LI
            for root_std_li in root_std_ul.find_all('li', recursive=False):
                standard = GradeParser._parse_standard_item(root_std_li)
                if standard:
                    result['standards'].append(standard)

                    # Count missing assignments
                    result['summary']['missing_assignments'] += standard.get('missing_count', 0)

        logger.info(f"Parsed {class_name}: "
                   f"{result['summary']['missing_assignments']} missing assignments")

        return result

    @staticmethod
    def _parse_standard_item(standard_element) -> Dict[str, Any]:
        """
        Parse a single standard item and its children recursively
        """
        from bs4 import BeautifulSoup

        standard = {
            'name': '',
            'score': '',
            'score_numeric': 0,
            'score_letter': '',
            'is_meeting': False,
            'children': [],
            'assignments': [],
            'missing_count': 0,
            'low_score_count': 0  # Count of assignments with grade < M (3.0)
        }

        # Get the standard data div
        std_data = standard_element.find('div', class_='standard-item-data')
        if not std_data:
            return None

        # Extract name
        std_desc = std_data.find('span', class_='standard-item-desc')
        if std_desc:
            standard['name'] = std_desc.get_text(strip=True)

        # Extract score
        std_score = std_data.find('span', class_='standard-item-score-inner')
        if std_score:
            score_text = std_score.get_text(strip=True)
            # Remove the chart icons from score text
            score_text = score_text.split('\n')[0].strip()
            standard['score'] = score_text

            # Parse numeric and letter grade (e.g., "2.35=P")
            if '=' in score_text:
                parts = score_text.split('=')
                try:
                    standard['score_numeric'] = float(parts[0])
                    standard['score_letter'] = parts[1]
                    # Trust the letter grade - M means meeting regardless of numeric score
                    standard['is_meeting'] = parts[1] == 'M'
                except (ValueError, IndexError):
                    pass

        # Find child standards (nested ul.standard-item)
        # Look for direct child ul elements
        for child_ul in standard_element.find_all('ul', class_='standard-item', recursive=False):
            for child_li in child_ul.find_all('li', recursive=False):
                child_std = GradeParser._parse_standard_item(child_li)
                if child_std:
                    standard['children'].append(child_std)
                    standard['missing_count'] += child_std.get('missing_count', 0)
                    standard['low_score_count'] += child_std.get('low_score_count', 0)

        # Find assignments table
        asn_container = standard_element.find('div', class_='divAsnContainer', recursive=False)
        if asn_container:
            assignments_table = asn_container.find('table', class_='assignmentTable')
            if assignments_table:
                tbody = assignments_table.find('tbody')
                if tbody:
                    for row in tbody.find_all('tr'):
                        assignment = GradeParser._parse_assignment_row(row)
                        if assignment:
                            standard['assignments'].append(assignment)
                            if assignment['is_missing']:
                                standard['missing_count'] += 1
                            # Count assignments that are below Meeting (grade < 3.0)
                            elif assignment['grade_numeric'] > 0 and assignment['grade_numeric'] < 3.0:
                                standard['low_score_count'] += 1

        return standard

    @staticmethod
    def _parse_assignment_row(row) -> Dict[str, Any]:
        """
        Parse a single assignment row from the table
        """
        assignment = {
            'due_date': '',
            'name': '',
            'weight': '',
            'grade': '',
            'grade_numeric': 0,
            'grade_letter': '',
            'is_missing': False,
            'is_late': False,
            'feedback': ''
        }

        cells = row.find_all('td')
        if len(cells) < 4:
            return None

        # Due date
        date_span = cells[0].find('span', class_='tablesaw-cell-content')
        if date_span:
            assignment['due_date'] = date_span.get_text(strip=True)

        # Assignment name
        name_span = cells[1].find('span', class_='tablesaw-cell-content')
        if name_span:
            name_link = name_span.find('a')
            if name_link:
                assignment['name'] = name_link.get_text(strip=True)
                # Check if it's red (missing)
                if name_link.get('style', '').find('color:red') >= 0:
                    assignment['is_missing'] = True

        # Weight
        weight_span = cells[2].find('span', class_='tablesaw-cell-content')
        if weight_span:
            assignment['weight'] = weight_span.get_text(strip=True)

        # Grade
        grade_span = cells[3].find('span', class_='tablesaw-cell-content')
        if grade_span:
            # Check for any status icon (Missing, Excused, Handed In, etc.)
            status_img = grade_span.find('img')
            if status_img and status_img.get('title'):
                status_text = status_img.get('title')
                assignment['grade'] = status_text
                if status_text == 'Missing':
                    assignment['is_missing'] = True
            else:
                grade_text = grade_span.get_text(strip=True)
                assignment['grade'] = grade_text

                # Parse numeric grade if available (e.g., "2.5=P")
                if '=' in grade_text:
                    parts = grade_text.split('=')
                    try:
                        assignment['grade_numeric'] = float(parts[0])
                        assignment['grade_letter'] = parts[1]
                    except (ValueError, IndexError):
                        pass

        # Feedback (optional, 5th column)
        if len(cells) > 4:
            feedback_span = cells[4].find('span', class_='tablesaw-cell-content')
            if feedback_span:
                assignment['feedback'] = feedback_span.get_text(strip=True)

        # Check for missing indicator in row attributes
        if row.get('data-bmissing') == '1':
            assignment['is_missing'] = True

        return assignment
