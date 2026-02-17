import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2_database.vector_store import VectorDatabase
from phase4_itinerary.prompts import get_itinerary_prompt, ITINERARY_SYSTEM_PROMPT
import logging
from typing import Dict, Any
import json
from datetime import datetime
from dotenv import load_dotenv

# Force load .env file at the very beginning
load_dotenv()
print(f"[DEBUG] [itinerary] - After load_dotenv(), GROQ_API_KEY exists: {bool(os.getenv('GROQ_API_KEY'))}")
if os.getenv('GROQ_API_KEY'):
    print(f"[DEBUG] [itinerary] - Key starts with: {os.getenv('GROQ_API_KEY')[:10]}...")
    print(f"[DEBUG] [itinerary] - Key length: {len(os.getenv('GROQ_API_KEY'))} characters")

try:
    from groq import Groq
except ImportError:
    os.system("pip install groq")
    from groq import Groq

# Try to import FPDF for PDF generation
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("[WARNING] fpdf not installed. PDF export disabled. Install with: pip install fpdf")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ItinerarySuggester:
    def __init__(self, api_key=None):
        """Initialize Itinerary Suggester"""
        print(f"\n[DEBUG] [itinerary] - ItinerarySuggester.__init__ called")
        print(f"[DEBUG] [itinerary] - Received api_key parameter: {api_key[:10] if api_key else 'None'}...")
        
        self.vector_db = VectorDatabase()
        
        # Initialize Groq
        env_key = os.getenv("GROQ_API_KEY")
        print(f"[DEBUG] [itinerary] - Environment GROQ_API_KEY: {env_key[:10] if env_key else 'None'}...")
        
        self.api_key = api_key or env_key
        print(f"[DEBUG] [itinerary] - Final api_key being used: {self.api_key[:10] if self.api_key else 'None'}...")
        print(f"[DEBUG] [itinerary] - API key length: {len(self.api_key) if self.api_key else 0} characters")
        
        if self.api_key:
            try:
                print(f"[DEBUG] [itinerary] - Attempting to create Groq client...")
                self.client = Groq(api_key=self.api_key)
                print(f"[DEBUG] [itinerary] - Groq client created successfully")
                
                print(f"[DEBUG] [itinerary] - Testing client with models.list()...")
                models = self.client.models.list()
                print(f"[DEBUG] [itinerary] - SUCCESS! Found {len(models.data)} models")
                
                self.llm_available = True
                logger.info("Groq client initialized successfully")
            except Exception as e:
                print(f"[DEBUG] [itinerary] - [ERROR] Groq initialization FAILED!")
                print(f"[DEBUG] [itinerary] - Error type: {type(e).__name__}")
                print(f"[DEBUG] [itinerary] - Error message: {e}")
                logger.warning(f"Groq initialization failed: {e}")
                self.llm_available = False
        else:
            print(f"[DEBUG] [itinerary] - No API key found in either parameter or environment")
            self.llm_available = False
            logger.warning("No API key found. Will use template-based suggestions.")
        
        # Load all tours
        self.load_tours()
    
    def load_tours(self):
        """Load tours from JSON"""
        try:
            # First try to load cleaned data
            with open('phase1_scraping/tour_data_cleaned.json', 'r', encoding='utf-8') as f:
                self.tours = json.load(f)
            logger.info(f"Loaded {len(self.tours)} tours from cleaned data")
        except FileNotFoundError:
            logger.warning("Cleaned data not found, trying raw data...")
            try:
                with open('phase1_scraping/tour_data.json', 'r', encoding='utf-8') as f:
                    self.tours = json.load(f)
                logger.info(f"Loaded {len(self.tours)} tours from raw data")
            except:
                self.tours = []
                logger.warning("No tour data found")
        except Exception as e:
            logger.error(f"Error loading tours: {e}")
            self.tours = []
    
    def get_relevant_context(self, location: str, interests: str) -> str:
        """Get relevant tour context for the location and interests"""
        query = f"{location} {interests} tour package itinerary"
        context = self.vector_db.get_context_for_query(query, n_results=8)
        return context if context else "No specific tour data found for this query."
    
    def collect_user_preferences(self) -> Dict[str, Any]:
        """Collect user preferences for itinerary"""
        print("\n" + "="*60)
        print("PLAN YOUR DREAM ITINERARY WITH NAMASTE INDIA TRIP")
        print("="*60)
        
        preferences = {}
        
        print("\nLet's understand your travel preferences:")
        
        # Location/Region
        print("\nPopular regions: Rajasthan, Kerala, Himachal, Uttarakhand, Tamil Nadu, Golden Triangle")
        preferences['location'] = input("Which region/state would you like to visit? ").strip()
        
        # Duration
        print("\n(Example: 5 days, 1 week, 10 days)")
        preferences['duration'] = input("How many days do you have? ").strip()
        
        # Interests
        print("\nInterests: Heritage, Adventure, Pilgrimage, Wildlife, Yoga, Food, Culture, Beaches, Hills")
        preferences['interests'] = input("What are your main interests? ").strip()
        
        # Budget level
        print("\nBudget: Budget (under $100/day), Moderate ($100-200/day), Luxury ($200+/day)")
        preferences['budget'] = input("What's your budget level? ").strip()
        
        # Travel style
        print("\nStyle: Relaxed, Fast-paced, Family-friendly, Romantic, Solo backpacker, Luxury")
        preferences['style'] = input("Preferred travel style? ").strip()
        
        # Special requirements
        preferences['special'] = input("Any special requirements or occasions? (Enter 'None' if none): ").strip()
        if not preferences['special']:
            preferences['special'] = "None"
        
        return preferences
    
    def generate_template_itinerary(self, preferences: Dict) -> str:
        """Generate a template itinerary when LLM is not available"""
        location = preferences.get('location', 'India')
        duration = preferences.get('duration', '7 days')
        interests = preferences.get('interests', 'sightseeing')
        budget = preferences.get('budget', 'moderate')
        style = preferences.get('style', 'relaxed')
        
        # Find matching tours
        matching_tours = []
        for tour in self.tours:
            tour_text = json.dumps(tour).lower()
            tour_destinations = [d.lower() for d in tour.get('destinations', [])]
            
            # Check if location matches any destination
            location_match = any(location.lower() in dest for dest in tour_destinations) or location.lower() in tour_text
            
            # Check if interests match
            interest_match = any(interest.lower() in tour_text for interest in interests.split(','))
            
            if location_match or interest_match:
                matching_tours.append(tour)
        
        if matching_tours:
            response = f"[ITINERARY] **Suggested Itinerary Template for {location}**\n\n"
            response += f"Based on your preferences:\n"
            response += f"• **Duration:** {duration}\n"
            response += f"• **Interests:** {interests}\n"
            response += f"• **Budget:** {budget}\n"
            response += f"• **Travel Style:** {style}\n\n"
            
            response += f"Here are some tours we recommend:\n\n"
            
            for i, tour in enumerate(matching_tours[:5], 1):
                response += f"{i}. **{tour.get('name', 'Unknown Tour')}**\n"
                response += f"   Duration: {tour.get('duration', 'Not specified')}\n"
                response += f"   Theme: {tour.get('theme', 'General')}\n"
                response += f"   Destinations: {', '.join(tour.get('destinations', [])[:3])}\n"
                if tour.get('highlights'):
                    response += f"   Highlights: {tour['highlights'][0][:100]}...\n"
                response += f"   Price: {tour.get('price', 'Contact for price')}\n\n"
            
            response += "\n[TIP] These tours can be customized to match your exact preferences. Contact our travel experts for a personalized quote!"
        else:
            response = f"[ITINERARY] **Itinerary Suggestion for {location}**\n\n"
            response += f"Based on your request for a {duration} trip focusing on {interests}, we recommend:\n\n"
            response += f"• Check our {location} tour packages on our website\n"
            response += f"• Contact our travel experts for a custom quote\n"
            response += f"• Explore nearby destinations that match your interests\n\n"
            response += "Please visit www.namasteindiatrip.com or call us for more information."
        
        return response
    
    def save_itinerary_as_pdf(self, preferences: Dict, itinerary: str) -> str:
        """Save generated itinerary as PDF file with proper encoding"""
        if not PDF_AVAILABLE:
            logger.warning("PDF export not available. Install fpdf package.")
            return None

        try:
            # Create PDF object with Unicode support
            pdf = FPDF()
            pdf.add_page()

            # Add a Unicode font that supports Indian Rupee symbol
            # Fallback to standard fonts with replacement for special characters

            # Set fonts
            pdf.set_font("Arial", "B", 16)

            # Title
            pdf.cell(200, 10, "Namaste India Trip", ln=True, align="C")
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, "Personalized Itinerary", ln=True, align="C")
            pdf.ln(10)

            # User Preferences
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, "Your Preferences:", ln=True)
            pdf.set_font("Arial", "", 11)

            for key, value in preferences.items():
                # Clean the text to remove problematic characters
                clean_value = str(value).encode('latin-1', errors='ignore').decode('latin-1')
                clean_key = key.capitalize().encode('latin-1', errors='ignore').decode('latin-1')
                text = f"{clean_key}: {clean_value}"
                pdf.multi_cell(0, 8, text)

            pdf.ln(5)

            # Itinerary content
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, "Your Personalized Itinerary:", ln=True)
            pdf.set_font("Arial", "", 11)

            # Split itinerary into lines and add to PDF
            lines = itinerary.split('\n')
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Remove or replace problematic characters
                    clean_line = line.replace('₹', 'Rs.').replace('→', '->').replace('•', '-')
                    clean_line = clean_line.encode('latin-1', errors='ignore').decode('latin-1')

                    # Handle bold text (marked with **)
                    if '**' in clean_line:
                        parts = clean_line.split('**')
                        for i, part in enumerate(parts):
                            if i % 2 == 1:  # Odd indices are between ** **
                                pdf.set_font("Arial", "B", 11)
                                pdf.write(5, part)
                                pdf.set_font("Arial", "", 11)
                            else:
                                pdf.write(5, part)
                        pdf.ln(5)
                    else:
                        pdf.multi_cell(0, 5, clean_line)

            # Add footer with date
            pdf.ln(10)
            pdf.set_font("Arial", "I", 8)
            pdf.cell(200, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.cell(200, 5, "Namaste India Trip - Your Trusted Travel Partner", ln=True)

            # Create itineraries folder if it doesn't exist
            os.makedirs('phase4_itinerary/generated_itineraries', exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location = preferences.get('location', 'unknown').replace(' ', '_').lower()
            filename = f"phase4_itinerary/generated_itineraries/itinerary_{location}_{timestamp}.pdf"

            # Save PDF
            pdf.output(filename)
            logger.info(f"Itinerary saved as PDF to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            return None
    
    def generate_itinerary(self, preferences: Dict) -> str:
        """Generate personalized itinerary"""
        logger.info(f"Generating itinerary for: {preferences}")
        
        # Get relevant context
        context = self.get_relevant_context(
            preferences.get('location', ''),
            preferences.get('interests', '')
        )
        
        if not self.llm_available:
            return self.generate_template_itinerary(preferences)
        
        try:
            # Generate prompt
            prompt = get_itinerary_prompt(preferences, context)
            
            print(f"[DEBUG] [itinerary] - Sending request to Groq API with model: llama-3.3-70b-versatile")
            
            # Call LLM with updated model
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            print(f"[DEBUG] [itinerary] - Groq API request successful")
            itinerary = completion.choices[0].message.content
            
            # OPTIONAL: You can keep server-side saving if needed, or comment it out
            # self.save_itinerary(preferences, itinerary)
            # self.save_itinerary_as_pdf(preferences, itinerary)
            
            logger.info("Itinerary generated successfully")
            return itinerary
            
        except Exception as e:
            print(f"[DEBUG] [itinerary] - [ERROR] Groq API call failed!")
            print(f"[DEBUG] [itinerary] - Error type: {type(e).__name__}")
            print(f"[DEBUG] [itinerary] - Error message: {e}")
            logger.error(f"Error generating itinerary: {e}")
            return self.generate_template_itinerary(preferences)
    
    def save_itinerary(self, preferences: Dict, itinerary: str) -> str:
        """Save generated itinerary to text file"""
        try:
            # Create itineraries folder if it doesn't exist
            os.makedirs('phase4_itinerary/generated_itineraries', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location = preferences.get('location', 'unknown').replace(' ', '_').lower()
            filename = f"phase4_itinerary/generated_itineraries/itinerary_{location}_{timestamp}.txt"
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("NAMASTE INDIA TRIP - PERSONALIZED ITINERARY\n")
                f.write("="*60 + "\n\n")
                
                f.write("USER PREFERENCES:\n")
                f.write("-"*30 + "\n")
                for key, value in preferences.items():
                    f.write(f"{key.capitalize()}: {value}\n")
                
                f.write("\nGENERATED ITINERARY:\n")
                f.write("-"*30 + "\n")
                f.write(itinerary)
                
                f.write("\n\n" + "="*60 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n")
            
            logger.info(f"Itinerary saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving itinerary: {e}")
            return None
    
    def run(self):
        """Main method to run the itinerary suggester"""
        print("\n" + "="*60)
        print("NAMASTE INDIA TRIP - AI ITINERARY PLANNER")
        print("="*60)
        
        if not self.llm_available:
            print("\n[INFO] Running in template mode (no AI).")
            print("   For AI-powered custom itineraries, get a free API key from:")
            print("   https://console.groq.com\n")
        else:
            print("\n[AI] AI-Powered Mode Enabled (using Llama 3.3 70B)")
        
        if PDF_AVAILABLE:
            print("[INFO] PDF export enabled")
        else:
            print("[INFO] PDF export not available (install fpdf for PDF support)")
        
        # Collect preferences
        preferences = self.collect_user_preferences()
        
        print("\n" + "="*60)
        print("Generating your personalized itinerary...")
        print("="*60)
        
        # Generate itinerary
        itinerary = self.generate_itinerary(preferences)
        
        # Display results
        print("\n" + "="*60)
        print("YOUR PERSONALIZED ITINERARY")
        print("="*60)
        print(itinerary)
        print("\n" + "="*60)
        
        # Notify user that itinerary was saved
        print("\n[SAVED] Your itinerary has been automatically saved to the 'generated_itineraries' folder:")
        location = preferences.get('location', 'unknown').replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"   • Text file: itinerary_{location}_{timestamp}.txt")
        if PDF_AVAILABLE:
            print(f"   • PDF file: itinerary_{location}_{timestamp}.pdf")
        
        # Ask if user wants to start over
        again = input("\nWould you like to plan another itinerary? (y/n): ").strip().lower()
        if again == 'y':
            self.run()
        else:
            print("\nThank you for using Namaste India Trip! Happy travels!\n")

def main():
    """Main function to run the itinerary suggester"""
    print("\n[DEBUG] [itinerary] - Starting main() function")
    
    # Get API key from environment or prompt user
    api_key = os.getenv("GROQ_API_KEY")
    print(f"[DEBUG] [itinerary] - os.getenv('GROQ_API_KEY') in main: {api_key[:10] if api_key else 'None'}...")
    
    if not api_key:
        print("\n[INFO] To use the AI-powered itinerary generator, get a free API key from:")
        print("   https://console.groq.com")
        print("\n   Without an API key, I'll use template-based suggestions.")
        use_ai = input("\nDo you want to enter your Groq API key now? (y/n): ").strip().lower()
        
        if use_ai == 'y':
            api_key = input("Enter your Groq API key: ").strip()
            if api_key:
                print(f"[DEBUG] [itinerary] - Manual API key entered: {api_key[:10]}...")
                print("[OK] API key set successfully!")
            else:
                print("[WARNING] No API key entered. Using template mode.")
    
    # Initialize and run
    print(f"[DEBUG] [itinerary] - Creating ItinerarySuggester with api_key: {api_key[:10] if api_key else 'None'}...")
    suggester = ItinerarySuggester(api_key=api_key)
    suggester.run()

if __name__ == "__main__":
    main()