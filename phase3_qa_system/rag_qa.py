import sys
import os
# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2_database.vector_store import VectorDatabase
import logging
from typing import Dict, Any
import json
from dotenv import load_dotenv

# Force load .env file at the very beginning
load_dotenv()
print(f"[DEBUG] - After load_dotenv(), GROQ_API_KEY exists: {bool(os.getenv('GROQ_API_KEY'))}")
if os.getenv('GROQ_API_KEY'):
    print(f"[DEBUG] - Key starts with: {os.getenv('GROQ_API_KEY')[:10]}...")
    print(f"[DEBUG] - Key length: {len(os.getenv('GROQ_API_KEY'))} characters")

try:
    from groq import Groq
except ImportError:
    print("Installing groq...")
    os.system("pip install groq")
    from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGQASystem:
    def __init__(self, api_key=None):
        """Initialize RAG QA System"""
        print(f"\n[DEBUG] - RAGQASystem.__init__ called")
        print(f"[DEBUG] - Received api_key parameter: {api_key[:10] if api_key else 'None'}...")
        
        self.vector_db = VectorDatabase()
        self.website_url = "https://www.namasteindiatrip.com"  # Add website URL
        
        # Initialize Groq client
        env_key = os.getenv("GROQ_API_KEY")
        print(f"[DEBUG] - Environment GROQ_API_KEY: {env_key[:10] if env_key else 'None'}...")
        
        self.api_key = api_key or env_key
        print(f"[DEBUG] - Final api_key being used: {self.api_key[:10] if self.api_key else 'None'}...")
        print(f"[DEBUG] - API key length: {len(self.api_key) if self.api_key else 0} characters")
        
        if self.api_key:
            try:
                print(f"[DEBUG] - Attempting to create Groq client...")
                self.client = Groq(api_key=self.api_key)
                print(f"[DEBUG] - Groq client created successfully")
                
                print(f"[DEBUG] - Testing client with models.list()...")
                models = self.client.models.list()
                print(f"[DEBUG] - SUCCESS! Found {len(models.data)} models")
                print(f"[DEBUG] - First 3 models available:")
                for i, model in enumerate(models.data[:3]):
                    print(f"           {i+1}. {model.id}")
                
                self.llm_available = True
                logger.info("Groq client initialized successfully")
                
                # List of available models (for reference)
                self.available_models = [
                    "llama-3.3-70b-versatile",  # Latest Llama 3.3 70B (recommended)
                    "llama-3.1-70b-versatile",  # Llama 3.1 70B
                    "llama3-70b-8192",           # Llama 3 70B
                    "gemma2-9b-it",               # Google Gemma 2 9B
                    "mixtral-8x7b-32768"          # Decommissioned - do not use
                ]
                
            except Exception as e:
                print(f"[DEBUG] - [ERROR] Groq initialization FAILED!")
                print(f"[DEBUG] - Error type: {type(e).__name__}")
                print(f"[DEBUG] - Error message: {e}")
                logger.warning(f"Groq initialization failed: {e}")
                logger.warning("Falling back to template-based responses")
                self.llm_available = False
        else:
            print(f"[DEBUG] - No API key found in either parameter or environment")
            self.llm_available = False
            logger.warning("No Groq API key found. Will use template-based responses.")
        
        # Load all tours for fallback
        self.tours = self.load_all_tours()
        print(f"[DEBUG] - Loaded {len(self.tours)} tours for fallback\n")
    
    def load_all_tours(self):
        """Load all tours from JSON"""
        try:
            # Use cleaned data instead of raw data
            with open('phase1_scraping/tour_data_cleaned.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("tour_data_cleaned.json not found. Trying raw data...")
            try:
                with open('phase1_scraping/tour_data.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        except Exception as e:
            logger.error(f"Error loading tours: {e}")
            return []
    
    def search_tours_by_keyword(self, query: str) -> list:
        """Simple keyword search as fallback"""
        results = []
        query_lower = query.lower()
        
        for tour in self.tours:
            score = 0
            # Check tour name
            if query_lower in tour.get('name', '').lower():
                score += 3
            # Check destinations
            for dest in tour.get('destinations', []):
                if query_lower in dest.lower():
                    score += 2
            # Check theme
            if query_lower in tour.get('theme', '').lower():
                score += 2
            # Check highlights
            for highlight in tour.get('highlights', []):
                if query_lower in highlight.lower():
                    score += 1
            
            if score > 0:
                results.append((tour, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:5]]
    
    def format_tour_for_response(self, tour: Dict) -> str:
        """Format tour data for response"""
        response = f"""
[TOUR] **{tour.get('name', 'Unknown Tour')}**
   Duration: {tour.get('duration', 'Not specified')}
   Theme: {tour.get('theme', 'General')}
   Destinations: {', '.join(tour.get('destinations', []))}
   Price: {tour.get('price', 'Contact for price')}
"""
        if tour.get('highlights'):
            response += "   Highlights:\n"
            for h in tour['highlights'][:3]:
                response += f"     • {h}\n"
        return response
    
    def answer_question(self, question: str) -> str:
        """Answer a question using RAG"""
        logger.info(f"Question: {question}")
        
        # Step 1: Retrieve relevant context
        context = self.vector_db.get_context_for_query(question, n_results=5)
        
        # Step 2: If no context from vector DB, use keyword search
        if not context:
            relevant_tours = self.search_tours_by_keyword(question)
            if relevant_tours:
                response = "**Based on your query, here are relevant tours:**\n\n"
                for tour in relevant_tours:
                    response += self.format_tour_for_response(tour)
                response += f"\n[TIP] For more options, visit our website: {self.website_url}"
                return response
            else:
                return f"""I couldn't find specific tours matching your query in our database. 

[SUGGESTIONS]
• Try different keywords (e.g., "Delhi" instead of "New Delhi")
• Browse our complete collection on our website
• Contact our travel experts for personalized assistance

[WEBSITE] Visit us at: {self.website_url}

Would you like help with something else?"""
        
        # Step 3: If LLM is available, generate intelligent response
        if self.llm_available:
            try:
                # IMPROVED PROMPT WITH BETTER FORMATTING INSTRUCTIONS
                prompt = f"""You are a helpful travel assistant for Namaste India Trip, a premium tour operator in India.

Use the following real tour information to answer the user's question. Be friendly, informative, and concise.

CONTEXT FROM OUR TOUR DATABASE:
{context}

USER QUESTION: {question}

IMPORTANT GUIDELINES:
1. Only use information from the context provided above
2. If specific details (price, duration, destinations) are missing, say so and offer to help get that information
3. For tours without listed destinations, explain they're customizable
4. For tours without prices, say "Price available on request" and offer to connect with sales team
5. Suggest similar tours when exact matches aren't found
6. Keep response under 200 words
7. Be enthusiastic about India travel!

**RESPONSE FORMATTING REQUIREMENTS:**
- Format your response with clear sections using **bold headings**
- Use bullet points (•) for listing multiple tours or features
- Put each tour on a new line with its key details
- Use line breaks between sections for readability
- Keep paragraphs short (2-3 sentences maximum)
- End with a friendly question to engage the user

EXAMPLE OF GOOD FORMATTING:
**Here are some tours I found for you:**

• **Delhi Sightseeing Tour** - 1 Day
  Perfect for exploring the capital's iconic landmarks.
  *Highlights:* Red Fort, Qutub Minar, India Gate

• **Delhi Agra Tour Package** - 3 Days/2 Nights
  Combine Delhi with the majestic Taj Mahal.
  *Price:* Available on request

Would you like more details about any of these options?

If no tours match the query, suggest visiting the website: {self.website_url}

YOUR ANSWER (follow the formatting example above):"""

                print(f"[DEBUG] - Sending request to Groq API with model: llama-3.3-70b-versatile")
                
                completion = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a knowledgeable travel assistant for Namaste India Trip. Always format your responses with clear sections, bold headings, and bullet points for readability. When no tours are found, politely suggest visiting the website. Do not use emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                print(f"[DEBUG] - Groq API request successful")
                return completion.choices[0].message.content
            
            except Exception as e:
                print(f"[DEBUG] - [ERROR] Groq API call failed!")
                print(f"[DEBUG] - Error type: {type(e).__name__}")
                print(f"[DEBUG] - Error message: {e}")
                logger.error(f"LLM error: {e}")
                # Fallback to context-based response with website link
                return f"""**Here's what I found about your query:**

{context}

[TIP] For more options, visit our website: {self.website_url}

Would you like me to help with something else?"""
        
        # Step 4: If no LLM, return formatted context with website link
        else:
            return f"""**Here's what I found in our tours database:**

{context}

[TIP] For more options, visit our website: {self.website_url}"""
    
    def interactive_mode(self):
        """Run interactive Q&A session"""
        print("\n" + "="*60)
        print("NAMASTE INDIA TRIP - TRAVEL ASSISTANT")
        print("="*60)
        
        if self.llm_available:
            print("\n[AI] AI-Powered Mode Enabled (using Llama 3.3 70B)")
        else:
            print("\n[INFO] Template Mode (no AI)")
            
        print("\nAsk me anything about our tours! (type 'quit' to exit)")
        print("Examples:")
        print("  • What pilgrimage tours do you offer?")
        print("  • Tell me about Rajasthan tours")
        print("  • Do you have any yoga packages?")
        print("  • What's the price of Golden Triangle Tour?")
        print("-"*60)
        
        while True:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using Namaste India Trip Assistant! Happy travels!")
                break
            
            if not question:
                continue
            
            print("\n[SEARCH] Searching our database...")
            answer = self.answer_question(question)
            print(f"\n[ANSWER]\n{answer}")
            print("\n" + "-"*60)

def main():
    """Main function to run the Q&A system"""
    print("\n[DEBUG] - Starting main() function")
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    print(f"[DEBUG] - os.getenv('GROQ_API_KEY') in main: {api_key[:10] if api_key else 'None'}...")
    
    if not api_key:
        print("\n[INFO] To use the AI-powered assistant, get a free API key from https://console.groq.com")
        print("   Without API key, I'll use template-based responses.")
        use_ai = input("\nDo you want to enter your Groq API key? (y/n): ").lower()
        
        if use_ai == 'y':
            api_key = input("Enter your Groq API key: ").strip()
            if api_key:
                print(f"[DEBUG] - Manual API key entered: {api_key[:10]}...")
                print("[OK] API key set successfully!")
            else:
                print("[WARNING] No API key entered. Using template mode.")
    
    # Initialize system
    print(f"[DEBUG] - Creating RAGQASystem with api_key: {api_key[:10] if api_key else 'None'}...")
    qa_system = RAGQASystem(api_key=api_key)
    
    # Start interactive mode
    qa_system.interactive_mode()

if __name__ == "__main__":
    main()