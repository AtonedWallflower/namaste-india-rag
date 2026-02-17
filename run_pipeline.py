#!/usr/bin/env python
"""
Complete Automation Pipeline for Namaste India Trip RAG System
Runs BOTH scrapers for maximum data collection, then cleans duplicates
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(text)
    print("="*70)

def print_step(step_num, total_steps, text):
    """Print a step indicator"""
    print(f"\n[{step_num}/{total_steps}] {text}")
    print("-"*50)

def run_command(command, description):
    """Run a shell command and print output"""
    print(f"\n[EXEC] {description}...")
    print(f"   $ {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in 
                      ['error', 'exception', 'traceback', 'found', 'saved', 
                       'cleaned', 'loaded', 'scraping', 'tour', 'success']):
                    print(f"   {line}")
        
        if result.returncode != 0:
            print(f"   [ERROR] Command failed with code {result.returncode}")
            if result.stderr:
                print(f"   {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")
        return False

def verify_file_exists(filepath, description):
    """Check if a file exists and return its size"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"   [OK] {description} found ({size:,} bytes)")
        return True
    else:
        print(f"   [ERROR] {description} not found: {filepath}")
        return False

def count_tours_in_json(filepath):
    """Count number of tours in a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data.get('tours', []))
            else:
                return 0
    except:
        return 0

def run_backup_scraper_fast():
    """Run the backup scraper in fast mode"""
    print("\n[BACKUP] Running fast backup scraper...")
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from phase1_scraping.backup_scraper import BackupScraper
        
        # Create scraper instance
        scraper = BackupScraper()
        
        # Override to use faster settings
        scraper.session.timeout = 10  # Shorter timeout
        print("[BACKUP] Using fast mode: 10 second timeout, limited tour pages")
        
        # Run the scraper
        tours = scraper.scrape_all()
        
        if tours:
            # Save to a temporary file first
            temp_file = 'phase1_scraping/backup_tours_temp.json'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(tours, f, indent=2, ensure_ascii=False)
            
            print(f"[BACKUP] Fast scraper found {len(tours)} tours")
            return True, tours
        else:
            print("[BACKUP] No tours found")
            return False, []
            
    except Exception as e:
        print(f"[BACKUP] Error: {e}")
        return False, []

def merge_tour_data(main_file, backup_tours):
    """Merge backup tours with existing main file"""
    try:
        # Load existing main data
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                main_tours = json.load(f)
            print(f"[MERGE] Loaded {len(main_tours)} tours from main file")
        else:
            main_tours = []
            print("[MERGE] No existing main file, creating new")
        
        # Combine tours
        all_tours = main_tours + backup_tours
        print(f"[MERGE] Total combined: {len(all_tours)} tours")
        
        # Quick in-memory deduplication (final cleaning will handle properly)
        seen = set()
        unique_tours = []
        for tour in all_tours:
            name = tour.get('name', '')
            if name and name not in seen:
                seen.add(name)
                unique_tours.append(tour)
        
        print(f"[MERGE] After quick dedup: {len(unique_tours)} tours")
        
        # Save merged data
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(unique_tours, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"[MERGE] Error: {e}")
        return False

def main():
    """Main pipeline execution"""
    
    print_header("NAMASTE INDIA TRIP - DUAL SCRAPER PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_steps = 6
    current_step = 0
    
    # Step 1: Check environment
    current_step += 1
    print_step(current_step, total_steps, "Checking Environment")
    
    required_dirs = ['phase1_scraping', 'phase2_database', 'phase3_qa_system', 'phase4_itinerary']
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    
    if missing_dirs:
        print(f"[ERROR] Missing directories: {missing_dirs}")
        return
    
    print("[OK] Project structure verified")
    
    # Step 2: Run primary scraper (Selenium-based)
    current_step += 1
    print_step(current_step, total_steps, "Running Primary Scraper (Selenium)")
    
    scraper_file = 'phase1_scraping/tab_navigator_scraper.py'
    primary_success = False
    
    if os.path.exists(scraper_file):
        print("[INFO] Starting Selenium-based scraper...")
        primary_success = run_command(
            f"python {scraper_file}",
            "Scraping all tour tabs with Selenium"
        )
        if primary_success:
            print("[OK] Primary scraper completed")
        else:
            print("[WARNING] Primary scraper had issues, but continuing...")
    else:
        print(f"[WARNING] Primary scraper not found at {scraper_file}")
    
    # Wait a moment for files to be written
    time.sleep(2)
    
    # Step 3: Run backup scraper (always runs, fast mode)
    current_step += 1
    print_step(current_step, total_steps, "Running Backup Scraper (Fast HTTP)")
    
    backup_success, backup_tours = run_backup_scraper_fast()
    
    if backup_success and backup_tours:
        print(f"[OK] Backup scraper found {len(backup_tours)} tours")
    else:
        print("[INFO] Backup scraper found no new tours")
        backup_tours = []
    
    # Step 4: Merge data (if backup found anything)
    current_step += 1
    print_step(current_step, total_steps, "Merging Tour Data")
    
    main_file = 'phase1_scraping/all_tours_complete.json'
    
    if backup_tours:
        merge_success = merge_tour_data(main_file, backup_tours)
        if merge_success:
            print("[OK] Data merged successfully")
        else:
            print("[WARNING] Merge had issues, but continuing...")
    else:
        print("[INFO] No backup tours to merge")
    
    # Verify main file exists
    if not verify_file_exists(main_file, "Combined tour data"):
        print("[ERROR] No tour data file found. Creating empty file.")
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    raw_count = count_tours_in_json(main_file)
    print(f"[STATS] Total raw tours before cleaning: {raw_count}")
    
    # Step 5: Run intelligent cleaner (handles ALL duplicates)
    current_step += 1
    print_step(current_step, total_steps, "Running Intelligent Cleaner (Removes Duplicates)")
    
    cleaner_file = 'phase1_scraping/intelligent_cleaner.py'
    if not os.path.exists(cleaner_file):
        print(f"[ERROR] Cleaner not found at {cleaner_file}")
        return
    
    cleaner_success = run_command(
        f"python {cleaner_file}",
        "Cleaning and deduplicating tour data"
    )
    
    if not cleaner_success:
        print("[ERROR] Cleaning failed. Exiting pipeline.")
        return
    
    # Verify cleaned data
    cleaned_file = 'phase1_scraping/tour_data_cleaned.json'
    if not verify_file_exists(cleaned_file, "Cleaned tour data"):
        print("[ERROR] Cleaner output not found. Exiting pipeline.")
        return
    
    cleaned_count = count_tours_in_json(cleaned_file)
    print(f"[STATS] Cleaned tours count: {cleaned_count}")
    print(f"[STATS] Duplicates removed: {raw_count - cleaned_count}")
    
    # Step 6: Rebuild database
    current_step += 1
    print_step(current_step, total_steps, "Rebuilding Vector Database")
    
    # Delete old database if it exists
    if os.path.exists('chroma_db'):
        print("   Removing old database...")
        try:
            if os.name == 'nt':  # Windows
                os.system('rmdir /s /q chroma_db 2>nul')
            else:  # Linux/Mac
                os.system('rm -rf chroma_db')
            print("   [OK] Old database removed")
        except Exception as e:
            print(f"   [WARNING] Could not remove old database: {e}")
    
    # Rebuild database
    db_script = 'phase2_database/vector_store.py'
    if not os.path.exists(db_script):
        print(f"[ERROR] Database script not found at {db_script}")
        return
    
    db_success = run_command(
        f"python {db_script}",
        "Building new vector database"
    )
    
    if not db_success:
        print("[ERROR] Database rebuild failed. Exiting pipeline.")
        return
    
    # Final Summary
    print("\n" + "="*70)
    print("PIPELINE SUMMARY")
    print("="*70)
    print(f"\n[OK] Pipeline completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\nSTATISTICS:")
    print(f"   • Primary scraper: {'✅ Success' if primary_success else '⚠️  Had issues'}")
    print(f"   • Backup scraper: {len(backup_tours)} tours found")
    print(f"   • Raw tours before cleaning: {raw_count}")
    print(f"   • Cleaned tours: {cleaned_count}")
    print(f"   • Duplicates removed: {raw_count - cleaned_count}")
    
    # Show theme distribution
    try:
        with open(cleaned_file, 'r', encoding='utf-8') as f:
            tours = json.load(f)
        
        theme_counts = {}
        for tour in tours:
            theme = tour.get('theme', 'General')
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        print(f"\nTOURS BY THEME:")
        for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count/cleaned_count)*100
            print(f"   • {theme}: {count} ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"\n   [WARNING] Could not load theme data: {e}")
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nNEXT STEPS:")
    print("   1. Run your Streamlit app:")
    print("      → streamlit run app.py")
    print("\n   2. Or run the Q&A system:")
    print("      → python phase3_qa_system/rag_qa.py")
    print("\n   3. Or run the itinerary planner:")
    print("      → python phase4_itinerary/itinerary_suggester.py")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)