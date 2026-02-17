\# 🧳 Namaste India Trip - AI Travel Assistant



A comprehensive RAG (Retrieval-Augmented Generation) system that provides intelligent travel assistance for Namaste India Trip, featuring web scraping, vector database, AI-powered Q\&A, and personalized itinerary generation.



\## 🚀 Features



\### 1. \*\*Dual Web Scrapers\*\*

\- \*\*Primary Scraper\*\*: Selenium-based tab navigator that explores all tour categories

\- \*\*Backup Scraper\*\*: Fast HTTP-based scraper for redundancy

\- Automatic data merging and deduplication



\### 2. \*\*Intelligent Data Processing\*\*

\- Cleans and enhances raw tour data

\- Removes UI noise and duplicate entries

\- Classifies tours by theme (Pilgrimage, Heritage, Adventure, etc.)

\- Calculates data completeness scores



\### 3. \*\*Vector Database\*\*

\- ChromaDB for efficient similarity search

\- 144+ quality tours indexed

\- Semantic search capabilities



\### 4. \*\*AI-Powered Q\&A System\*\*

\- Groq integration with Llama 3.3 70B model

\- Context-aware responses using RAG

\- Formatted, human-readable answers



\### 5. \*\*Personalized Itinerary Planner\*\*

\- Generates custom travel plans based on user preferences

\- AI-powered itinerary creation

\- Download as Text or PDF



\### 6. \*\*Streamlit Web Application\*\*

\- Clean, modern UI with three main tabs:

&nbsp; - 💬 Chat Assistant

&nbsp; - 🗺️ Itinerary Planner

&nbsp; - 📚 Tour Explorer

\- Interactive data visualization

\- Responsive design



\## 📋 Prerequisites



\- Python 3.11

\- Conda (recommended) or pip

\- Groq API key (free from https://console.groq.com)



\## 🛠️ Installation



\### Using Conda (Recommended)



```bash

\# Clone the repository

git clone https://github.com/AtonedWallflower/namaste-india-rag.git

cd namaste-india-rag



\# Create conda environment

conda env create -f environment.yml

conda activate namaste-rag

