import os
import sys
import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'ERROR': 30
}

# Get log level from environment or default to INFO
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
if LOG_LEVEL not in LOG_LEVELS:
    LOG_LEVEL = 'INFO'

def log(message, level='INFO'):
    """Simple logging function."""
    if LOG_LEVELS[level] >= LOG_LEVELS[LOG_LEVEL]:
        print(f"[{level}] {message}")

def get_webpage_content(url):
    """Fetch and parse webpage content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        log(f"Response status code: {response.status_code}", 'DEBUG')
        log(f"Response text: {response.text}", 'DEBUG')
        exit()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Log the content if in DEBUG mode
        log("Webpage content:", 'DEBUG')
        log("-" * 50, 'DEBUG')
        log(text, 'DEBUG')
        log("-" * 50, 'DEBUG')
        
        return text
    except Exception as e:
        log(f"Error fetching webpage: {e}", 'ERROR')
        sys.exit(1)

def extract_event_info(content):
    """Extract event information using OpenAI."""
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        prompt = f"""
        Please analyze the following event webpage content and extract the event details. Be precise and thorough.
        YOU MUST FIND THE DATE AND TIME OF THE EVENT.  IT IS VERY IMPORTANT.
        If other information is not found, return "Not specified" for that field.

        Please return the information in this exact format:
        Event Title:
        Event Description:
        Event Location:
        Event Date:
        Event Start Time:
        Event End Time:
        Event Cost:
        Event Host:
        Number of Attendees:
        Additional Details:
        - Agenda:
        - Requirements:
        - Special Notes:

        For the Additional Details section, please organize information under the appropriate subsections (Agenda, Requirements, Special Notes).
        Use bullet points for better readability.

        Text content:
        {content}
        """
        
        log("Sending request to OpenAI...", 'DEBUG')
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a precise event information extractor. Extract all details accurately, maintaining the exact format specified. Format the output cleanly with proper line breaks and bullet points.  Date and Time are very important.  The Date can appear on the webpage like: DayOfWeek, MonthName, Date. e.g Thursday, April 10"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=1000
        )
        return response.choices[0].message['content']
    except Exception as e:
        log(f"Error with OpenAI API: {e}", 'ERROR')
        sys.exit(1)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check if URL is provided as command line argument
    if len(sys.argv) != 2:
        log("Usage: python extract_event.py <url>", 'ERROR')
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Get webpage content
    log("Fetching webpage content...", 'INFO')
    content = get_webpage_content(url)
    
    # Extract event information
    log("\nExtracting event information using GPT-4...", 'INFO')
    event_info = extract_event_info(content)
    
    # Print results
    print("\nExtracted Event Information:")
    print("-" * 50)
    print(event_info)

if __name__ == "__main__":
    main() 