import streamlit as st
import sys
import os
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules
from phase3_qa_system.rag_qa import RAGQASystem
from phase4_itinerary.itinerary_suggester import ItinerarySuggester

# Page configuration
st.set_page_config(
    page_title="Namaste India Trip - AI Travel Assistant",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
        padding-top: 1rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    
    .assistant-message {
        background-color: #ffffff;
        border-left: 5px solid #4caf50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        line-height: 1.6;
    }
    
    /* Improved readability for assistant responses */
    .assistant-message p {
        margin-bottom: 0.8rem;
    }
    
    .assistant-message ul, .assistant-message ol {
        margin-left: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    .assistant-message li {
        margin-bottom: 0.3rem;
    }
    
    .assistant-message strong {
        color: #2e7d32;
    }
    
    .assistant-message h3, .assistant-message h4 {
        color: #1b5e20;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Itinerary card styling */
    .itinerary-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .itinerary-card h1, .itinerary-card h2, .itinerary-card h3 {
        color: #FF4B4B;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .itinerary-card ul, .itinerary-card ol {
        margin-left: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Tour card styling */
    .tour-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 0.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .tour-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Dropdown cursor styling */
    .stSelectbox, .stMultiSelect, .stRadio {
        cursor: pointer;
    }
    
    .stSelectbox:hover, .stMultiSelect:hover, .stRadio:hover {
        cursor: pointer;
    }
    
    .stSelectbox > div > div {
        cursor: pointer !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        cursor: pointer !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        cursor: pointer !important;
    }
    
    /* Button styling */
    .stButton > button {
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #FF4B4B;
        color: white;
    }
    
    /* Link styling */
    .homepage-link {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    .homepage-link a {
        color: #FF4B4B;
        text-decoration: none;
        font-weight: bold;
    }
    
    .homepage-link a:hover {
        text-decoration: underline;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        cursor: pointer;
        font-size: 1.1rem;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #FF4B4B;
    }
    
    /* Stats cards */
    .stat-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #FF4B4B;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Divider */
    .custom-divider {
        margin: 2rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #FF4B4B, transparent);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'itinerary_suggester' not in st.session_state:
    st.session_state.itinerary_suggester = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'tours_data' not in st.session_state:
    st.session_state.tours_data = None
if 'current_itinerary' not in st.session_state:
    st.session_state.current_itinerary = None
if 'current_preferences' not in st.session_state:
    st.session_state.current_preferences = None

# Check API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("""
    ❌ **GROQ_API_KEY not found!**
    
    Please create a `.env` file in the project root with:
    ```
    GROQ_API_KEY=gsk_your_actual_key_here
    ```
    
    Get your free key from: https://console.groq.com
    """)
    st.stop()

# Load tours data
@st.cache_data
def load_tours_data():
    try:
        with open('phase1_scraping/tour_data_cleaned.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# Initialize systems
@st.cache_resource
def init_rag_system():
    return RAGQASystem(api_key=api_key)

@st.cache_resource
def init_itinerary_suggester():
    return ItinerarySuggester(api_key=api_key)

# Initialize
if st.session_state.rag_system is None:
    with st.spinner("🔄 Initializing AI systems..."):
        st.session_state.rag_system = init_rag_system()
        st.session_state.itinerary_suggester = init_itinerary_suggester()

if st.session_state.tours_data is None:
    st.session_state.tours_data = load_tours_data()

# Main header
st.markdown('<h1 class="main-header">🧳 Namaste India Trip</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your AI-Powered Travel Assistant for Incredible India</p>', unsafe_allow_html=True)

# Quick stats row
if st.session_state.tours_data:
    tours = st.session_state.tours_data
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="stat-card"><div class="stat-number">' + str(len(tours)) + '</div><div class="stat-label">Total Tours</div></div>', unsafe_allow_html=True)
    
    with col2:
        pilgrimage = sum(1 for t in tours if t.get('theme') == 'Pilgrimage')
        st.markdown('<div class="stat-card"><div class="stat-number">' + str(pilgrimage) + '</div><div class="stat-label">Pilgrimage</div></div>', unsafe_allow_html=True)
    
    with col3:
        international = sum(1 for t in tours if t.get('theme') == 'International')
        st.markdown('<div class="stat-card"><div class="stat-number">' + str(international) + '</div><div class="stat-label">International</div></div>', unsafe_allow_html=True)
    
    with col4:
        romantic = sum(1 for t in tours if t.get('theme') == 'Romantic')
        st.markdown('<div class="stat-card"><div class="stat-number">' + str(romantic) + '</div><div class="stat-label">Romantic</div></div>', unsafe_allow_html=True)
    
    with col5:
        adventure = sum(1 for t in tours if t.get('theme') == 'Adventure')
        st.markdown('<div class="stat-card"><div class="stat-number">' + str(adventure) + '</div><div class="stat-label">Adventure</div></div>', unsafe_allow_html=True)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# Create tabs for main features
tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "🗺️ Itinerary Planner", "📚 Tour Explorer"])

# Tab 1: Chat Assistant
with tab1:
    st.markdown("### 💬 Ask Me Anything About Tours")
    st.markdown("Get personalized recommendations and information about tours, destinations, and travel in India.")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Format assistant responses for better readability
                formatted_response = message["content"]
                # Remove multiple "Namaste!" occurrences
                formatted_response = formatted_response.replace("Namaste! ", "").replace("Namaste, ", "")
                # Ensure first greeting is appropriate
                if formatted_response.startswith("Namaste"):
                    formatted_response = "👋 " + formatted_response[7:]
                st.markdown(f'<div class="assistant-message">{formatted_response}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask about tours, destinations, prices..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag_system.answer_question(prompt)
                # Clean the response
                cleaned_response = response.replace("Namaste! ", "").replace("Namaste, ", "")
                if cleaned_response.startswith("Namaste"):
                    cleaned_response = "👋 " + cleaned_response[7:]
                st.markdown(f'<div class="assistant-message">{cleaned_response}</div>', unsafe_allow_html=True)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

# Tab 2: Itinerary Planner - Updated PDF generation
with tab2:
    st.markdown("### 🗺️ Create Your Perfect Itinerary")
    st.markdown("Tell us your preferences and we'll create a personalized travel plan.")
    
    with st.form("itinerary_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("📍 Destination", placeholder="e.g., Rajasthan, Kerala, Delhi")
            duration = st.text_input("⏱️ Duration", placeholder="e.g., 7 days, 2 weeks")
            interests = st.text_input("🎯 Interests", placeholder="e.g., heritage, food, adventure")
        
        with col2:
            budget = st.selectbox("💰 Budget", ["Budget", "Moderate", "Luxury"])
            style = st.selectbox("🚶 Travel Style", ["Relaxed", "Fast-paced", "Family-friendly", "Solo backpacker", "Romantic"])
            special = st.text_input("✨ Special Requirements", placeholder="e.g., honeymoon, meditation")
        
        submitted = st.form_submit_button("Generate Itinerary", use_container_width=True)
    
    if submitted:
        preferences = {
            'location': location,
            'duration': duration,
            'interests': interests,
            'budget': budget,
            'style': style,
            'special': special if special else "None"
        }
        
        with st.spinner("Creating your personalized itinerary..."):
            itinerary = st.session_state.itinerary_suggester.generate_itinerary(preferences)
        
        # Store in session state
        st.session_state.current_itinerary = itinerary
        st.session_state.current_preferences = preferences
        
        # Display the itinerary
        st.markdown('<div class="itinerary-card">', unsafe_allow_html=True)
        st.markdown(itinerary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download options
        st.markdown("### 📥 Download Your Itinerary")
        col1, col2 = st.columns(2)
        
        with col1:
            # Text file download
            text_filename = f"itinerary_{location.lower().replace(' ', '_')}.txt"
            st.download_button(
                label="📄 Download as Text File",
                data=itinerary,
                file_name=text_filename,
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # PDF download - FIXED VERSION
            try:
                from fpdf import FPDF
                import io
                import time
                
                # Create PDF in memory using BytesIO
                pdf_buffer = io.BytesIO()
                
                pdf = FPDF()
                pdf.add_page()
                
                # Title
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, "Namaste India Trip", ln=True, align="C")
                pdf.set_font("Arial", "B", 14)
                pdf.cell(200, 10, "Personalized Itinerary", ln=True, align="C")
                pdf.ln(10)
                
                # Preferences
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, "Your Preferences:", ln=True)
                pdf.set_font("Arial", "", 11)
                for key, value in preferences.items():
                    clean_value = str(value).replace('₹', 'Rs.').replace('→', '-').replace('•', '-')
                    clean_key = key.capitalize()
                    pdf.cell(200, 8, f"{clean_key}: {clean_value}", ln=True)
                pdf.ln(10)
                
                # Itinerary
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, "Your Personalized Itinerary:", ln=True)
                pdf.set_font("Arial", "", 11)
                
                lines = itinerary.split('\n')
                for line in lines:
                    if line.strip():
                        clean_line = line.replace('₹', 'Rs.').replace('→', '-').replace('•', '-')
                        pdf.multi_cell(0, 5, clean_line)
                
                # Footer
                pdf.ln(10)
                pdf.set_font("Arial", "I", 8)
                pdf.cell(200, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
                
                # Output to BytesIO instead of file
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                # Download button with BytesIO data
                pdf_filename = f"itinerary_{location.lower().replace(' ', '_')}.pdf"
                st.download_button(
                    label="📕 Download as PDF",
                    data=pdf_output,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
                st.info("You can still download the text version above.")
    
    # Show last generated itinerary if available
    elif st.session_state.current_itinerary and st.session_state.current_preferences:
        st.markdown("### 📥 Your Last Generated Itinerary")
        st.markdown(f"**Destination:** {st.session_state.current_preferences.get('location', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        with col1:
            text_filename = f"itinerary_{st.session_state.current_preferences.get('location', 'itinerary').lower().replace(' ', '_')}.txt"
            st.download_button(
                label="📄 Download Last Itinerary as Text",
                data=st.session_state.current_itinerary,
                file_name=text_filename,
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # PDF download for last itinerary - FIXED VERSION
            try:
                from fpdf import FPDF
                import io
                
                # Create PDF in memory using BytesIO
                pdf_buffer = io.BytesIO()
                
                pdf = FPDF()
                pdf.add_page()
                
                # Title
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, "Namaste India Trip", ln=True, align="C")
                pdf.set_font("Arial", "B", 14)
                pdf.cell(200, 10, "Personalized Itinerary", ln=True, align="C")
                pdf.ln(10)
                
                # Preferences from session state
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, "Your Preferences:", ln=True)
                pdf.set_font("Arial", "", 11)
                for key, value in st.session_state.current_preferences.items():
                    clean_value = str(value).replace('₹', 'Rs.').replace('→', '-').replace('•', '-')
                    clean_key = key.capitalize()
                    pdf.cell(200, 8, f"{clean_key}: {clean_value}", ln=True)
                pdf.ln(10)
                
                # Itinerary from session state
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, "Your Personalized Itinerary:", ln=True)
                pdf.set_font("Arial", "", 11)
                
                lines = st.session_state.current_itinerary.split('\n')
                for line in lines:
                    if line.strip():
                        clean_line = line.replace('₹', 'Rs.').replace('→', '-').replace('•', '-')
                        pdf.multi_cell(0, 5, clean_line)
                
                # Footer
                pdf.ln(10)
                pdf.set_font("Arial", "I", 8)
                pdf.cell(200, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
                
                # Output to string and encode
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                pdf_filename = f"itinerary_{st.session_state.current_preferences.get('location', 'itinerary').lower().replace(' ', '_')}.pdf"
                st.download_button(
                    label="📕 Download Last Itinerary as PDF",
                    data=pdf_output,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"PDF generation failed for last itinerary: {e}")
# Tab 3: Tour Explorer
with tab3:
    st.markdown("### 📚 Browse Our Tour Collection")
    st.markdown("Explore our curated collection of tours and packages.")
    
    if st.session_state.tours_data:
        tours = st.session_state.tours_data
        
        # Filters - Only Theme and Search
        col1, col2 = st.columns(2)
        with col1:
            themes = ["All"] + sorted(set(t.get('theme', 'General') for t in tours))
            selected_theme = st.selectbox("Filter by Theme", themes, key="theme_filter")
        with col2:
            search = st.text_input("Search tours", placeholder="Enter keywords...", key="search_filter")
        
        # Apply filters
        filtered_tours = tours
        
        # Filter by theme
        if selected_theme != "All":
            filtered_tours = [t for t in filtered_tours if t.get('theme') == selected_theme]
        
        # Filter by search
        if search:
            filtered_tours = [t for t in filtered_tours if search.lower() in json.dumps(t).lower()]
        
        # Display tours
        st.markdown(f"### Found {len(filtered_tours)} tours")
        
        if not filtered_tours:
            st.info("No tours match your filters. Try adjusting your criteria.")
        
        for tour in filtered_tours:
            with st.expander(f"📍 {tour.get('name')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Theme:** {tour.get('theme', 'General')}")
                    st.markdown(f"**Duration:** {tour.get('duration', 'Not specified')}")
                    if tour.get('destinations') and tour['destinations'] != ["Destinations available on request"]:
                        st.markdown(f"**Destinations:** {', '.join(tour['destinations'][:5])}")
                    if tour.get('highlights') and tour['highlights'] != ["Customizable tour package - contact for details"]:
                        st.markdown("**Highlights:**")
                        for h in tour['highlights'][:3]:
                            st.markdown(f"- {h}")
                
                with col2:
                    price = tour.get('price', 'Contact for price')
                    st.markdown(f"**Price:** {price}")
                    
                    if 'metadata' in tour:
                        score = tour['metadata'].get('completeness_score', 0)
                        st.progress(score/100, text=f"Details: {score}%")
                    
                    if st.button("📞 Contact for Details", key=f"btn_{tour.get('name')}"):
                        st.info("📧 Email: info@namasteindiatrip.com\n\n📞 Phone: +91-123-456-7890")
    else:
        st.warning("No tour data found. Please run the scraper first.")

# Homepage link at the bottom
st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
st.markdown("""
<div class="homepage-link">
    🌐 Visit our main website for more information: 
    <a href="https://www.namasteindiatrip.com" target="_blank">www.namasteindiatrip.com</a>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0; font-size: 0.9rem;">
    Powered by Namaste India Trip • Your Trusted Travel Partner Since 2014
</div>
""", unsafe_allow_html=True)