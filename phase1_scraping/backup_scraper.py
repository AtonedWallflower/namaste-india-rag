import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

class BackupScraper:
    """
    Backup scraper that uses direct HTTP requests
    Optimized for speed
    """
    
    def __init__(self):
        self.base_url = "https://www.namasteindiatrip.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.timeout = 10  # Fast timeout
        
        # Known tour category URLs
        self.category_urls = [
            {"name": "India Tours", "url": "/india-tour-packages"},
            {"name": "International Tours", "url": "/international-tours"},
            {"name": "Pilgrimage Tours", "url": "/pilgrimage-tours"},
            {"name": "Buddhist Tours", "url": "/buddhist-pilgrimage-tour-packages"},
            {"name": "Honeymoon Tours", "url": "/honeymoon-tour-package"},
            {"name": "Helicopter Tours", "url": "/helicopter-packages"},
            {"name": "Group Tours", "url": "/group-tour"},
        ]
    
    def fetch_page_fast(self, url):
        """Fast page fetch with minimal retries"""
        try:
            response = self.session.get(url, timeout=8)  # Fast 8 second timeout
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None
    
    def scrape_category_fast(self, category):
        """Fast category scraping - only get tour names and basic info"""
        url = self.base_url + category['url']
        html = self.fetch_page_fast(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        tours = []
        
        # Fast method: Look for tour links and extract basic info
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            if ('tour' in href.lower() or 'package' in href.lower()) and len(text) > 15:
                if href.startswith('/'):
                    # Basic tour info without fetching individual pages
                    tour = {
                        'name': text,
                        'url': self.base_url + href,
                        'category': category['name'],
                        'duration': '',
                        'destinations': [],
                        'highlights': [],
                        'price': '',
                        'theme': self.classify_theme(text + ' ' + category['name'])
                    }
                    
                    # Try to get price from link text or nearby text
                    price_match = re.search(r'[₹$€]\s*[\d,]+', text)
                    if price_match:
                        tour['price'] = price_match.group(0)
                    
                    tours.append(tour)
        
        # Limit to first 15 per category for speed
        return tours[:15]
    
    def scrape_all_fast(self):
        """Fast scrape of all categories"""
        print("\n[BACKUP FAST] Starting fast backup scrape...")
        
        all_tours = []
        for i, category in enumerate(self.category_urls, 1):
            print(f"   [BACKUP] Scanning {category['name']}...")
            tours = self.scrape_category_fast(category)
            all_tours.extend(tours)
            print(f"      Found {len(tours)} tours")
        
        print(f"\n[BACKUP FAST] Total tours found: {len(all_tours)}")
        return all_tours
    
    def scrape_all(self):
        """Main method - calls fast version"""
        return self.scrape_all_fast()
    
    def classify_theme(self, text):
        """Classify tour theme based on text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['pilgrim', 'yatra', 'dham', 'temple']):
            return 'Pilgrimage'
        elif any(word in text_lower for word in ['heritage', 'rajasthan', 'palace']):
            return 'Heritage'
        elif any(word in text_lower for word in ['wildlife', 'safari']):
            return 'Wildlife'
        elif any(word in text_lower for word in ['yoga', 'meditation']):
            return 'Wellness'
        elif any(word in text_lower for word in ['honeymoon', 'romantic']):
            return 'Romantic'
        elif any(word in text_lower for word in ['beach', 'island']):
            return 'Beach'
        elif any(word in text_lower for word in ['adventure', 'trek']):
            return 'Adventure'
        elif any(word in text_lower for word in ['buddhist', 'circuit']):
            return 'Spiritual'
        elif any(word in text_lower for word in ['helicopter']):
            return 'Helicopter Tours'
        elif any(word in text_lower for word in ['group']):
            return 'Group Tours'
        elif any(word in text_lower for word in ['international', 'vietnam', 'thailand']):
            return 'International'
        else:
            return 'General'

if __name__ == "__main__":
    scraper = BackupScraper()
    tours = scraper.scrape_all()
    
    # Save to temp file
    with open('phase1_scraping/backup_tours_temp.json', 'w', encoding='utf-8') as f:
        json.dump(tours, f, indent=2, ensure_ascii=False)
    print(f"\n[BACKUP] Saved {len(tours)} tours to backup_tours_temp.json")