from playwright.sync_api import sync_playwright
import sys
import os
from dotenv import load_dotenv
import openai

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
    """Fetch webpage content using Playwright."""
    try:
        with sync_playwright() as p:
            # Launch the browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            log(f"Navigating to {url}...", 'INFO')
            
            # Navigate to the URL
            page.goto(url, wait_until='load')
            
            # Wait for the body to be present
            log(f"Wait for the body to be present", 'INFO')
            page.wait_for_selector('body')
            
            # Get the page content
            content = page.content()
            
            # Get the text content
            text = page.evaluate('() => document.body.innerText')
            
            log("Successfully loaded page", 'DEBUG')
            log(f"Page title: {page.title()}", 'DEBUG')
            
            # Close the browser
            browser.close()
            
            return text
            
    except Exception as e:
        log(f"Error loading webpage: {e}", 'ERROR')
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
        log("Usage: python load_page.py <url>", 'ERROR')
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Get webpage content
    log("Fetching webpage content...", 'INFO')
    content = get_webpage_content(url)
    # Print results
    print("\nWebpage Content:")
    print("-" * 50)
    print(content)

    # Extract event information
    log("\nExtracting event information using GPT-4...", 'INFO')
    event_info = extract_event_info(content)
    print("\nEvent Information:")
    print("-" * 50)
    print(event_info)

if __name__ == "__main__":
    main() 