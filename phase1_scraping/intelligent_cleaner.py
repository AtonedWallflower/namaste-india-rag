import json
import re
import os

def calculate_completeness(tour):
    """Calculate how complete the tour data is (0-100)"""
    score = 0
    if tour.get('name') and not any(x in tour['name'] for x in ['Package', 'Tour']):
        score += 10
    if tour.get('destinations') and tour['destinations'] != ["Destinations available on request"]:
        score += 30
    if tour.get('price') and tour['price'] != "Contact for price":
        score += 25
    if tour.get('duration') and tour['duration'] != "Duration varies by package":
        score += 25
    if tour.get('highlights') and tour['highlights'] != ["Customizable tour package - contact for details"]:
        score += 10
    return score

def enhance_tour_data(tour):
    """Enhance individual tour data"""
    
    # Clean up destinations
    if tour.get('destinations'):
        # Handle both list and string formats
        if isinstance(tour['destinations'], list):
            tour['destinations'] = [d.strip() for d in tour['destinations'] if d.strip()]
        elif isinstance(tour['destinations'], str):
            # Split by common separators
            text = tour['destinations']
            if '→' in text:
                tour['destinations'] = [d.strip() for d in text.split('→')]
            elif ',' in text:
                tour['destinations'] = [d.strip() for d in text.split(',') if d.strip()]
            else:
                tour['destinations'] = [text.strip()]
    
    # Ensure price is present
    if not tour.get('price') or tour['price'] == '' or 'On Request' in tour['price']:
        tour['price'] = "Contact for price"
    
    # Ensure destinations is present
    if not tour.get('destinations') or len(tour['destinations']) == 0:
        tour['destinations'] = ["Destinations available on request"]
    
    # Ensure duration is present
    if not tour.get('duration') or tour['duration'] == '':
        tour['duration'] = "Duration varies by package"
    else:
        # Clean up duration text
        tour['duration'] = re.sub(r'\s+', ' ', tour['duration'])
    
    # Ensure highlights is present
    if not tour.get('highlights') or len(tour['highlights']) == 0:
        tour['highlights'] = ["Customizable tour package - contact for details"]
    
    # Classify theme if missing
    if not tour.get('theme') or tour['theme'] == 'General':
        tour['theme'] = classify_tour_theme(tour)
    
    # Add metadata
    tour['metadata'] = {
        'has_destinations': bool(tour.get('destinations') and tour['destinations'] != ["Destinations available on request"]),
        'has_price': bool(tour.get('price') and tour['price'] != "Contact for price"),
        'has_duration': bool(tour.get('duration') and tour['duration'] != "Duration varies by package"),
        'has_highlights': bool(tour.get('highlights') and tour['highlights'] != ["Customizable tour package - contact for details"]),
        'completeness_score': calculate_completeness(tour)
    }
    
    return tour

def classify_tour_theme(tour):
    """Classify tour based on name and destinations"""
    name = tour.get('name', '')
    dest_text = ' '.join(tour.get('destinations', []))
    text = (name + ' ' + dest_text).lower()
    
    # International destinations
    international_keywords = ['vietnam', 'thailand', 'singapore', 'malaysia', 'dubai', 
                             'bali', 'egypt', 'sri lanka', 'nepal', 'bhutan', 'japan', 
                             'mauritius', 'europe', 'turkey', 'hong kong', 'macau', 
                             'phuket', 'pattaya', 'bangkok', 'koh samui', 'colombo', 
                             'kuala lumpur']
    
    if any(word in text for word in ['yatra', 'dham', 'pilgrim', 'temple', 'holy', 'shrine', 'darshan', 'jyotirlinga']):
        return 'Pilgrimage'
    elif any(word in text for word in ['rajasthan', 'palace', 'fort', 'heritage', 'royal', 'golden triangle']):
        return 'Heritage'
    elif any(word in text for word in ['yoga', 'meditation', 'wellness', 'ayurveda']):
        return 'Wellness'
    elif any(word in text for word in ['wildlife', 'safari', 'national park', 'jungle', 'corbett', 'ranthambore']):
        return 'Wildlife'
    elif any(word in text for word in ['honeymoon', 'romantic']):
        return 'Romantic'
    elif any(word in text for word in ['beach', 'island', 'andaman', 'goa', 'maldives']):
        return 'Beach'
    elif any(word in text for word in ['adventure', 'trek', 'ladakh', 'himachal']):
        return 'Adventure'
    elif any(word in text for word in ['buddhist', 'circuit', 'lumbini', 'bodhgaya', 'sarnath', 'kushinagar']):
        return 'Spiritual'
    elif any(word in text for word in ['helicopter']):
        return 'Helicopter Tours'
    elif any(word in text for word in ['group']):
        return 'Group Tours'
    elif any(word in text for word in international_keywords):
        return 'International'
    else:
        return 'General'

def save_statistics(tours):
    """Save data quality statistics"""
    total = len(tours)
    
    with_destinations = sum(1 for t in tours if t.get('destinations') and t['destinations'] != ["Destinations available on request"])
    with_price = sum(1 for t in tours if t.get('price') and t['price'] != "Contact for price")
    with_duration = sum(1 for t in tours if t.get('duration') and t['duration'] != "Duration varies by package")
    with_highlights = sum(1 for t in tours if t.get('highlights') and t['highlights'] != ["Customizable tour package - contact for details"])
    
    # Theme distribution
    theme_counts = {}
    for tour in tours:
        theme = tour.get('theme', 'General')
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    stats = {
        'total_tours': total,
        'tours_with_destinations': with_destinations,
        'tours_with_price': with_price,
        'tours_with_duration': with_duration,
        'tours_with_highlights': with_highlights,
        'destinations_percentage': round((with_destinations/total)*100, 1) if total > 0 else 0,
        'price_percentage': round((with_price/total)*100, 1) if total > 0 else 0,
        'duration_percentage': round((with_duration/total)*100, 1) if total > 0 else 0,
        'highlights_percentage': round((with_highlights/total)*100, 1) if total > 0 else 0,
        'theme_distribution': theme_counts
    }
    
    with open('phase1_scraping/data_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print("\n" + "="*60)
    print("DATA QUALITY STATISTICS")
    print("="*60)
    print(f"Total tours: {stats['total_tours']}")
    
    print(f"\n Data Completeness:")
    print(f"   • With destinations: {stats['tours_with_destinations']} ({stats['destinations_percentage']}%)")
    print(f"   • With price: {stats['tours_with_price']} ({stats['price_percentage']}%)")
    print(f"   • With duration: {stats['tours_with_duration']} ({stats['duration_percentage']}%)")
    print(f"   • With highlights: {stats['tours_with_highlights']} ({stats['highlights_percentage']}%)")
    
    print(f"\n Theme Distribution:")
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = round((count/total)*100, 1)
        print(f"   • {theme}: {count} ({percentage}%)")
    print("="*60)

def display_sample_tours(tours, count=15):
    """Display sample of cleaned tours"""
    print(f"\n Sample of {count} cleaned tours:")
    print("="*80)
    
    # Filter to show actual tours (not headers)
    actual_tours = [t for t in tours if any(indicator in t['name'] for indicator in 
                   ['Yatra', 'Tour', 'Package', 'Helicopter', 'Honeymoon'])]
    
    for i, tour in enumerate(actual_tours[:count], 1):
        print(f"{i}. {tour.get('name')}")
        print(f"   Theme: {tour.get('theme', 'General')}")
        if tour.get('destinations') and tour['destinations'] != ["Destinations available on request"]:
            dest_display = tour['destinations'][:3]
            print(f"   Destinations: {', '.join(dest_display)}")
        if tour.get('price') and tour['price'] != "Contact for price":
            print(f"   Price: {tour.get('price')}")
        if tour.get('duration') and tour['duration'] != "Duration varies by package":
            print(f"   Duration: {tour.get('duration')}")
        print(f"   Completeness: {tour['metadata']['completeness_score']}/100")
        print()

def intelligent_clean():
    """Intelligently clean tour data by removing UI noise while preserving real tours"""
    
    # Try multiple possible filenames
    possible_files = [
        'phase1_scraping/all_tours_complete.json'
    ]
    
    tours = None
    file_used = None
    
    for filename in possible_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tours = json.load(f)
                file_used = filename
                print(f"Loaded data from: {filename}")
                break
        except FileNotFoundError:
            continue
    
    if tours is None:
        print("  ERROR: Could not find any tour data file!")
        print("   Please run the scraper first:")
        print("   python phase1_scraping/tab_navigator_scraper.py")
        return []
    
    print(f"\n Loaded {len(tours)} raw entries from {file_used}")
    
    # === ENHANCED DUPLICATE DETECTION USING COMPLETENESS SCORE ===
    print("\n[INFO] Performing enhanced duplicate detection...")
    unique_tours = {}
    duplicates_found = 0
    
    for tour in tours:
        name = tour.get('name', '').strip()
        
        # Skip empty names
        if not name or len(name) < 5:
            continue
        
        # Check if we've seen this name before
        if name in unique_tours:
            duplicates_found += 1
            # Keep the version with higher completeness score
            existing_score = calculate_completeness(unique_tours[name])
            new_score = calculate_completeness(tour)
            if new_score > existing_score:
                unique_tours[name] = tour  # Replace with better version
        else:
            unique_tours[name] = tour
    
    print(f"[INFO] Found {duplicates_found} duplicate names")
    print(f"[INFO] After deduplication: {len(unique_tours)} unique tours")
    
    # Replace tours with deduplicated list
    tours = list(unique_tours.values())
    # === END OF ENHANCED DUPLICATE DETECTION ===
    
    # Define patterns for UI noise (things that are definitely not tours)
    ui_noise_patterns = [
        r'^India Tour Packages \| Ministry Approved \| Namaste India Trip$',
        r'^Ministry of Tourism,$',
        r'^MENUMENUIndia Tours$',
        r'^International Tours$',
        r'^Group ToursHelicopter ToursPilgrimage ToursBuddhist ToursHoneymoon ToursCustomer Center$',
        r'^Top Trending Tour Packages$',
        r'^Our Popular India Tour Packages$',
        r'^Book International Tour Packages From India$',
        r'^View Tour$',
        r'^View More Packages$',
        r'^Choose Your Style of Tour$',
        r'^Recognized by Ministry',
        r'^Chardham Yatra from Delhi$',
        r'^Chardham Yatra by Helicopter$',
        r'^Uttar Pradesh Tour Package$',
        r'^Madhya Pradesh Tour$',
        r'^Sri Lanka Ramayana Tour$',
        r'^Singapore Malaysia Tour$',
        r'^Thailand Tour Package$',
        r'^Dubai Tour Package$',
        r'^Bali Honeymoon Tour$',
        r'^Ujjain Omkareshwar Tour$',
        r'^Jagannath Puri Tour$',
        r'^Dwarka Somnath Tour$',
        r'^India Tour Packages$',
        r'^Uttarakhand Tour Packages$',
        r'^Kashmir Tour Packages$',
        r'^Himachal Tour Packages$',
        r'^Uttar Pradesh Tour Packages$',
        r'^Rajasthan Tour Packages$',
        r'^Madhya Pradesh Tour Packages$',
        r'^Goa Tour Packages$',
        r'^Tamil Nadu Tour Packages$',
        r'^Kerala Tour Packages$',
        r'^Orissa Tour Packages$',
        r'^Delhi Tour Packages$',
        r'^Gujarat Tour Packages$',
        r'^International Tour Packages$',
        r'^Europe Tour Packages$',
        r'^Asia Tour Packages$',
        r'^Sri Lanka Tour Packages$',
        r'^Dubai Tour Packages$',
        r'^Bali Tour Packages$',
        r'^Thailand Tour Packages$',
        r'^Singapore Tour Packages$',
        r'^Bhutan Tour Packages$',
        r'^Nepal Tour Packages$',
        r'^Malaysia Tour Packages$',
        r'^Egypt Tour Packages$',
        r'^Hong Kong Tour Packages$',
        r'^Trending Tour Packages$',
        r'^Pilgrimage Tour Packages$',
        r'^Honeymoon Tour Packages$',
        r'^Adventure Tours$',
        r'^Cruise Tours$',
        r'^Private Jet Tours$',
        r'^Speciality Tour$',
        r'^India Group Tour',
        r'^Fixed Departure',
        r'^Luxury Helicopter',
        r'^Helicopter Packages',
        r'^Buddhist Pilgrimage Tour',
        r'^10\+',
        r'^Q\d+:',
        r'^FAQs?',
        r'^Destinations ➝',
        r'^Popular',
        r'^Tour Cost\s*:',
    ]
    
    # Keywords that indicate a real tour (keep these)
    tour_indicators = [
        'Yatra', 'Tour', 'Package', 'Darshan', 'Helicopter', 
        'Temple', 'Pilgrimage', 'Heritage', 'Wildlife', 'Safari',
        'Golden Triangle', 'Rajasthan', 'Kerala', 'Goa', 'Ladakh',
        'Honeymoon', 'Adventure', 'Yoga', 'Meditation', 'Ayurveda',
        'Buddhist', 'Circuit', 'Char Dham', 'Amarnath', 'Kedarnath',
        'Badrinath', 'Gangotri', 'Yamunotri', 'Rameshwaram', 'Madurai',
        'Kanyakumari', 'Mahabalipuram', 'Khajuraho', 'Varanasi',
        'Ayodhya', 'Bodhgaya', 'Chitrakoot', 'Dwarka', 'Somnath',
        'Shirdi', 'Bhimashankar', 'Jyotirlinga', 'Muktinath',
        'Kailash', 'Mansarovar', 'Andaman', 'Sikkim', 'Darjeeling',
        'Orchha', 'Puri', 'Konark', 'Bhubaneswar', 'Guwahati',
        'Kamakhya', 'Nepal', 'Bhutan', 'Sri Lanka', 'Maldives',
        'Singapore', 'Malaysia', 'Thailand', 'Dubai', 'Bali',
        'Egypt', 'Vietnam', 'Japan', 'Mauritius', 'Europe',
        'Turkey', 'Hong Kong', 'Macau', 'Phuket', 'Pattaya',
        'Bangkok', 'Koh Samui', 'Colombo', 'Sigiriya', 'Kandy',
        'Nuwara Eliya', 'Beruwala', 'Abu Dhabi', 'Kuala Lumpur',
        'Thimphu', 'Paro', 'Vaishno Devi', 'Manimahesh', 'Haridwar',
        'Rishikesh', 'Allahabad', 'Ayodhya', 'Gaya', 'Bodhgaya',
        'Sarnath', 'Kushinagar', 'Lumbini', 'Sravasti', 'Rajgir',
        'Nalanda', 'Ajanta', 'Ellora', 'Ooty', 'Kashmir', 'Gulmarg',
        'Pahalgam', 'Sonmarg', 'Baltal', 'Neelgrath'
    ]
    
    cleaned_tours = []
    seen_names = set()
    
    print("\n Cleaning tour data...")
    
    for tour in tours:
        name = tour.get('name', '').strip()
        
        # Skip if name is empty or too short
        if not name or len(name) < 5:
            continue
        
        # Skip if matches UI noise patterns
        if any(re.match(pattern, name, re.I) for pattern in ui_noise_patterns):
            continue
        
        # Skip if name is all caps or all digits
        if name.isupper() or name.isdigit():
            continue
        
        # Skip duplicates (though we already did enhanced dedup, this is extra safety)
        if name in seen_names:
            continue
        
        # Check if it's likely a real tour
        is_real_tour = False
        
        # Check for tour indicators in name
        if any(indicator.lower() in name.lower() for indicator in tour_indicators):
            is_real_tour = True
        
        # Check if it has price or destinations (strong indicator of real tour)
        if tour.get('price') and tour['price'] not in ['', 'Contact for price', 'On Request']:
            is_real_tour = True
        
        # Keep if it has duration
        if tour.get('duration') and tour['duration'] not in ['', 'Duration varies by package']:
            is_real_tour = True
        
        # Keep if it has a URL pointing to a tour page
        if tour.get('url') and ('tour' in tour['url'].lower() or 'package' in tour['url'].lower()):
            is_real_tour = True
        
        if is_real_tour:
            # Clean up the tour data
            cleaned_tour = enhance_tour_data(tour)
            
            # Final name cleanup
            cleaned_name = cleaned_tour.get('name', '')
            cleaned_name = re.sub(r'\s+', ' ', cleaned_name)  # Remove extra spaces
            cleaned_name = re.sub(r'^\d+\+?\s*', '', cleaned_name)  # Remove leading numbers
            cleaned_tour['name'] = cleaned_name
            
            seen_names.add(cleaned_name)
            cleaned_tours.append(cleaned_tour)
            
            if len(cleaned_tours) % 20 == 0:
                print(f" Cleaned {len(cleaned_tours)} tours...")
    
    print(f"\n Kept {len(cleaned_tours)} quality tours out of {len(tours)} raw entries")
    
    # Save cleaned data
    output_file = 'phase1_scraping/tour_data_cleaned.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_tours, f, indent=2, ensure_ascii=False)
    print(f"Saved cleaned data to {output_file}")
    
    # Save statistics
    save_statistics(cleaned_tours)
    
    return cleaned_tours

if __name__ == "__main__":
    cleaned = intelligent_clean()
    if cleaned:
        display_sample_tours(cleaned)
        print(f"\n Cleaning complete! {len(cleaned)} quality tours ready for your RAG system!")