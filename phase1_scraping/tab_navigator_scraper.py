import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup  # IMPORTANT: Add this line!

class TabNavigatorScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome options"""
        print("\n" + "="*60)
        print("NAMASTE INDIA TRIP - TAB NAVIGATOR SCRAPER")
        print("="*60)
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.all_tours = []
        self.tabs_data = {}
        
    def discover_tabs(self):
        """Find all tour category tabs on the homepage"""
        print("\n Discovering tour tabs...")
        self.driver.get("https://www.namasteindiatrip.com")
        time.sleep(3)  # Wait for page to load
        
        # Common tab identifiers from the website
        tab_keywords = [
            "india tours", "international tours", "group tours", 
            "helicopter tours", "pilgrimage tours", "buddhist tours", 
            "honeymoon tours", "wildlife tours", "heritage tours",
            "yoga tours", "adventure tours", "beach tours"
        ]
        
        tabs_found = []
        
        # Method 1: Look for navigation menu items
        nav_elements = self.driver.find_elements(By.CSS_SELECTOR, 
            "nav a, .menu a, .navigation a, .navbar a, .nav-menu a, .main-menu a")
        
        for element in nav_elements:
            try:
                text = element.text.lower().strip()
                href = element.get_attribute('href')
                
                if text and href and any(keyword in text for keyword in tab_keywords):
                    if href not in [t['url'] for t in tabs_found]:
                        tabs_found.append({
                            'name': element.text.strip(),
                            'url': href,
                            'element': element
                        })
                        print(f" Found tab: {element.text.strip()} -> {href}")
            except:
                continue
        
        # Method 2: Look for dropdown menu items
        dropdown_items = self.driver.find_elements(By.CSS_SELECTOR, 
            ".dropdown-menu a, .submenu a, .megamenu a")
        
        for element in dropdown_items:
            try:
                text = element.text.lower().strip()
                href = element.get_attribute('href')
                
                if text and href and len(text) > 3 and text not in ['home', 'contact']:
                    if href not in [t['url'] for t in tabs_found]:
                        tabs_found.append({
                            'name': element.text.strip(),
                            'url': href,
                            'element': element
                        })
                        print(f" Found sub-tab: {element.text.strip()}")
            except:
                continue
        
        print(f"\n Found {len(tabs_found)} unique tabs to scrape")
        return tabs_found
    
    def scrape_tab(self, tab_info):
        """Scrape all tours from a specific tab"""
        print(f"\n Scraping tab: {tab_info['name']}")
        
        try:
            # Navigate to the tab URL
            self.driver.get(tab_info['url'])
            time.sleep(3)  # Wait for page to load
            
            # Scroll to load all content
            self.scroll_page()
            
            # Extract tours from this page
            tours = self.extract_tours_from_page(tab_info['name'])
            
            print(f"  Found {len(tours)} tours in {tab_info['name']}")
            return tours
            
        except Exception as e:
            print(f"  Error scraping {tab_info['name']}: {e}")
            return []
    
    def scroll_page(self):
        """Scroll the page to load lazy-loaded content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 5
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Calculate new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_height = new_height
        
        print("Finished scrolling")
    
    def extract_tours_from_page(self, tab_name):
        """Extract tour information from the current page"""
        tours = []
        
        # Try different selectors that might contain tour cards
        selectors = [
            ".tour-card", ".package-card", ".tour-item", ".package-item",
            ".product-card", ".tour-box", ".package-box", ".grid-item",
            ".col-md-4", ".col-lg-4", ".col-sm-6", ".col-xs-12",
            "article", ".item", ".card", ".tour", ".package",
            ".tour-list-item", ".package-list-item", ".destination-card"
        ]
        
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try each selector
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"   Found {len(elements)} elements with selector: {selector}")
                for element in elements[:30]:  # Limit to prevent overload
                    tour = self.parse_tour_element(element, tab_name)
                    if tour and tour.get('name') and len(tour.get('name', '')) > 10:
                        tours.append(tour)
                if tours:
                    print(f"Extracted {len(tours)} tours using {selector}")
                    break
        
        # If no structured elements found, try text-based extraction
        if not tours:
            print("   No structured elements found, trying text extraction...")
            tours = self.extract_tours_from_text(page_source, tab_name)
        
        return tours
    
    def parse_tour_element(self, element, tab_name):
        """Parse a single tour element"""
        try:
            tour = {}
            
            # Get tour name - try multiple selectors
            name_elem = (element.find(['h2', 'h3', 'h4']) or 
                        element.find('strong') or 
                        element.find(class_=re.compile(r'title|name', re.I)))
            
            if not name_elem:
                # Try to find any link with substantial text
                link = element.find('a', href=True)
                if link and len(link.get_text(strip=True)) > 15:
                    tour['name'] = link.get_text(strip=True)
                else:
                    return None
            else:
                tour['name'] = name_elem.get_text(strip=True)
            
            # Skip if name is too short or looks like noise
            if len(tour['name']) < 10 or any(x in tour['name'].lower() for x in ['view', 'click', 'read more']):
                return None
            
            # Get tour link
            link_elem = element.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    tour['url'] = 'https://www.namasteindiatrip.com' + href
                elif href.startswith('http'):
                    tour['url'] = href
            
            # Get text content
            text = element.get_text()
            
            # Extract duration
            duration_match = re.search(r'(\d+\s*(?:night|day|Nights|Days)[^\n]*)', text, re.I)
            if duration_match:
                tour['duration'] = duration_match.group(1).strip()
            
            # Extract price
            price_match = re.search(r'([₹$€]\s*[\d,]+|[A-Z]{3}\s*[\d,]+)', text)
            if price_match:
                tour['price'] = price_match.group(1).strip()
            
            # Extract destinations
            if '→' in text:
                dest_match = re.search(r'([^→\n]+(?:→[^→\n]+)+)', text)
                if dest_match:
                    tour['destinations'] = [d.strip() for d in dest_match.group(1).split('→')]
            
            # Extract highlights
            highlights = []
            bullet_points = element.find_all(['li', '.highlight', '.feature', '.inclusion'])
            for bullet in bullet_points[:3]:
                bullet_text = bullet.get_text(strip=True)
                if bullet_text and len(bullet_text) > 10:
                    highlights.append(bullet_text)
            if highlights:
                tour['highlights'] = highlights
            
            # Add metadata
            tour['source_tab'] = tab_name
            tour['theme'] = self.classify_theme(tour.get('name', '') + ' ' + tab_name)
            
            return tour
            
        except Exception as e:
            return None
    
    def extract_tours_from_text(self, html, tab_name):
        """Fallback: extract tours from raw text"""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        tours = []
        current_tour = {}
        
        for line in lines:
            # Look for tour indicators
            if ('Tour' in line or 'Package' in line or 'Yatra' in line) and len(line) < 100:
                if current_tour and 'name' in current_tour:
                    current_tour['source_tab'] = tab_name
                    current_tour['theme'] = self.classify_theme(current_tour.get('name', '') + ' ' + tab_name)
                    tours.append(current_tour)
                
                current_tour = {
                    'name': line,
                    'duration': '',
                    'destinations': [],
                    'highlights': [],
                    'price': ''
                }
            
            elif re.search(r'\d+\s*(?:night|day|Nights|Days)', line, re.I) and current_tour:
                current_tour['duration'] = line
            
            elif '→' in line and current_tour:
                current_tour['destinations'] = [d.strip() for d in line.split('→')]
            
            elif re.search(r'[₹$€]\s*[\d,]+', line) and current_tour:
                current_tour['price'] = line
        
        if current_tour and 'name' in current_tour:
            current_tour['source_tab'] = tab_name
            current_tour['theme'] = self.classify_theme(current_tour.get('name', '') + ' ' + tab_name)
            tours.append(current_tour)
        
        return tours
    
    def classify_theme(self, text):
        """Classify tour theme based on text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['pilgrim', 'yatra', 'dham', 'temple', 'holy', 'shrine']):
            return 'Pilgrimage'
        elif any(word in text_lower for word in ['heritage', 'rajasthan', 'palace', 'fort', 'golden triangle']):
            return 'Heritage'
        elif any(word in text_lower for word in ['wildlife', 'safari', 'national park', 'jungle']):
            return 'Wildlife'
        elif any(word in text_lower for word in ['yoga', 'meditation', 'wellness', 'ayurveda']):
            return 'Wellness'
        elif any(word in text_lower for word in ['honeymoon', 'romantic']):
            return 'Romantic'
        elif any(word in text_lower for word in ['beach', 'island', 'andaman', 'goa', 'maldives']):
            return 'Beach'
        elif any(word in text_lower for word in ['adventure', 'trek', 'ladakh', 'himachal']):
            return 'Adventure'
        elif any(word in text_lower for word in ['buddhist', 'circuit']):
            return 'Spiritual'
        elif any(word in text_lower for word in ['helicopter']):
            return 'Helicopter Tours'
        elif any(word in text_lower for word in ['group']):
            return 'Group Tours'
        elif any(word in text_lower for word in ['international', 'vietnam', 'thailand', 'singapore', 'dubai']):
            return 'International'
        else:
            return 'General'
    
    def scrape_all_tabs(self):
        """Main method to scrape all tabs"""
        # Discover all tabs
        tabs = self.discover_tabs()
        
        if not tabs:
            print("No tabs found! Trying direct URLs...")
            # Use your exact URLs
            common_urls = [
                {"name": "India Tours", "url": "https://www.namasteindiatrip.com/india-tour-packages"},
                {"name": "International Tours", "url": "https://www.namasteindiatrip.com/international-tours"},
                {"name": "Pilgrimage Tours", "url": "https://www.namasteindiatrip.com/pilgrimage-tours"},
                {"name": "Buddhist Tours", "url": "https://www.namasteindiatrip.com/buddhist-pilgrimage-tour-packages"},
                {"name": "Honeymoon Tours", "url": "https://www.namasteindiatrip.com/honeymoon-tour-package"},
                {"name": "Helicopter Tours", "url": "https://www.namasteindiatrip.com/helicopter-packages"},
                {"name": "Group Tours", "url": "https://www.namasteindiatrip.com/group-tour"}
            ]
            tabs = [{'name': t['name'], 'url': t['url']} for t in common_urls]
        
        # Scrape each tab
        all_tours = []
        for i, tab in enumerate(tabs, 1):
            print(f"\n[{i}/{len(tabs)}] Processing: {tab['name']}")
            tours = self.scrape_tab(tab)
            all_tours.extend(tours)
            
            # Add to tab data
            self.tabs_data[tab['name']] = {
                'url': tab['url'],
                'tour_count': len(tours)
            }
            
            # Small delay between tabs
            if i < len(tabs):
                time.sleep(2)
        
        # Remove duplicates
        unique_tours = {}
        for tour in all_tours:
            name = tour.get('name', '')
            if name and name not in unique_tours and len(name) > 10:
                unique_tours[name] = tour
        
        self.all_tours = list(unique_tours.values())
        
        # Print summary
        self.print_summary()
        
        # Save data
        self.save_data()
        
        return self.all_tours
    
    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Total tours found: {len(self.all_tours)}")
        
        print("\n Tours by Tab:")
        for tab_name, data in self.tabs_data.items():
            if data['tour_count'] > 0:
                print(f"   • {tab_name}: {data['tour_count']} tours")
        
        # Count by theme
        theme_counts = {}
        for tour in self.all_tours:
            theme = tour.get('theme', 'General')
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        if theme_counts:
            print("\n Tours by Theme:")
            for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {theme}: {count}")
        
        print("="*60)
    
    def save_data(self):
        """Save all tours to JSON file"""
        filename = 'phase1_scraping/all_tours_complete.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_tours, f, indent=2, ensure_ascii=False)
        print(f"\n Saved {len(self.all_tours)} tours to {filename}")
        
        # Also save categorized data
        categorized = {
            'by_tab': self.tabs_data,
            'tours': self.all_tours
        }
        
        with open('phase1_scraping/categorized_tours.json', 'w', encoding='utf-8') as f:
            json.dump(categorized, f, indent=2, ensure_ascii=False)
        print(f"Saved categorized data to phase1_scraping/categorized_tours.json")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()
        print("\n Browser closed.")

if __name__ == "__main__":
    scraper = TabNavigatorScraper(headless=False)  # Set to True to run in background
    try:
        tours = scraper.scrape_all_tabs()
        print(f"\n Successfully scraped {len(tours)} tours!")
    finally:
        scraper.close()