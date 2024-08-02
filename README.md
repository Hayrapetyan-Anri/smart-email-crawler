## README

### How to Run the Script

1. **Install Required Libraries:**
   Make sure you have Python installed. Then, install the required libraries using pip:
   ```bash
   pip install aiohttp beautifulsoup4 selenium webdriver-manager
   ```

2. **Configure the Script:**
   - Open the script in your preferred text editor.
   - Replace the placeholders for `CSE_ID` and `API_KEY` with your actual Custom Search Engine ID and API Key.

3. **Run the Script:**
   Save the script as `email_scraper.py` and run it using Python:
   ```bash
   python email_scraper.py
   ```

4. **Output:**
   The script will log the found emails and save them.

### Prerequisites
- Python 3.x
- Google Custom Search API Key
- Custom Search Engine ID

### Script Overview
- Fetches up to 100 URLs from Google Custom Search.
- Extracts emails using `requests` with `BeautifulSoup` and `Selenium` for robustness.
- Logs found emails.
