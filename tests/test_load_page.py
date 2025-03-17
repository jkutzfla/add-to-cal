import pytest
from unittest.mock import patch, MagicMock
import os
from load_page import extract_event_info
from save_to_calendar import parse_datetime
from dotenv import load_dotenv
# Sample test data
SAMPLE_WEBPAGE_CONTENT = """
Tech Conference 2024
Join us for an exciting day of technology talks and networking!

When: Thursday, April 25, 2024
Time: 9:00 AM - 5:00 PM
Location: Tech Hub, 123 Innovation Street, Silicon Valley
Cost: $299
Host: TechEvents Inc.

Limited to 200 attendees
"""

EXPECTED_GPT_RESPONSE = """Event Title: Tech Conference 2024
Event Description: An exciting day of technology talks and networking
Event Location: Tech Hub, 123 Innovation Street, Silicon Valley
Event Date: Thursday, April 25, 2024
Event Start Time: 9:00 AM
Event End Time: 5:00 PM
Event Cost: $299
Event Host: TechEvents Inc.
Number of Attendees: 200
Additional Details:
- Agenda: Not specified
- Requirements: Not specified
- Special Notes: Not specified"""

@pytest.fixture
def mock_openai_response():
    return MagicMock(choices=[
        MagicMock(message=MagicMock(content=EXPECTED_GPT_RESPONSE))
    ])

def test_extract_event_info_successful(mock_openai_response):
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-api-key'}):
            result = extract_event_info(SAMPLE_WEBPAGE_CONTENT)
            
            # Verify the result contains expected information
            assert 'Tech Conference 2024' in result
            assert 'Thursday, April 25, 2024' in result
            assert '9:00 AM' in result
            assert '5:00 PM' in result
            assert 'Tech Hub' in result
            assert '$299' in result
            assert 'TechEvents Inc.' in result

def test_extract_event_info_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            extract_event_info(SAMPLE_WEBPAGE_CONTENT)
        assert "OPENAI_API_KEY environment variable is not set" in str(exc_info.value)

def test_extract_event_info_api_error():
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-api-key'}):
            with pytest.raises(Exception) as exc_info:
                extract_event_info(SAMPLE_WEBPAGE_CONTENT)
            assert "API Error" in str(exc_info.value) 

def test_extract_event_info_missing_required_fields():
    load_dotenv()
    result = extract_event_info(SAMPLE_WEBPAGE_CONTENT)
    print(f"Result: {result}")
    assert "Event Title: Tech Conference 2024" in result
    # assert "Event Description: An exciting day of technology talks and networking" in result
    assert "Event Location: Tech Hub, 123 Innovation Street, Silicon Valley" in result
    assert "Event Date: 2024-04-25" in result
    assert "Event Start Time: 09:00:00" in result
    assert "Event End Time: 17:00:00" in result

def test_date_time_conversion():
    found_date = "2024-12-31"
    found_time = "09:00"

    parsed_date = parse_datetime(found_date, found_time)
    print(f"Parsed date: {parsed_date}")
    assert parsed_date is not None
    assert parsed_date.strftime("%Y-%m-%d %H:%M:%S") == "2024-12-31 09:00:00"
    assert parsed_date.isoformat() == "2024-12-31T09:00:00"

    found_date = "2025-03-18"
    found_time = "12:30:00"

    parsed_date = parse_datetime(found_date, found_time)
    print(f"Parsed date: {parsed_date}")
    assert parsed_date is not None
    assert parsed_date.strftime("%Y-%m-%d %H:%M:%S") == "2025-03-18 12:30:00"
    assert parsed_date.isoformat() == "2025-03-18T12:30:00"
