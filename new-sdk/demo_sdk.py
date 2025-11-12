#!/usr/bin/env python3
"""
Interactive CLI demo for BrightData SDK.

Tests the SDK with real API calls to verify:
- Client initialization
- Connection testing
- Generic web scraping
- Platform-specific scrapers
- Hierarchical interface
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from: {env_file}")
    else:
        print("⚠️  No .env file found, using system environment variables")
except ImportError:
    print("⚠️  python-dotenv not installed")

from brightdata import BrightDataClient
from brightdata.scrapers import get_registered_platforms

print("=" * 80)
print("🚀 BRIGHTDATA SDK - INTERACTIVE CLI DEMO")
print("=" * 80)
print()

# ============================================================================
# Step 1: Initialize Client
# ============================================================================

print("📋 Step 1: Initialize Client")
print("-" * 80)

try:
    client = BrightDataClient()
    print(f"✅ Client initialized: {client}")
    print(f"   Token: {client.token[:15]}...{client.token[-5:]}")
    print(f"   Timeout: {client.timeout}s")
    print(f"   Web Unlocker Zone: {client.web_unlocker_zone}")
    print()
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    print()
    print("Make sure BRIGHTDATA_API_TOKEN is set in your environment or .env file")
    sys.exit(1)

# ============================================================================
# Step 2: Test Connection
# ============================================================================

print("🔌 Step 2: Test Connection")
print("-" * 80)

async def test_connection():
    async with client:
        is_connected = await client.test_connection()
        
        if is_connected:
            print("✅ Connection successful!")
            
            # Get account info
            info = await client.get_account_info()
            print(f"   Zones: {info['zone_count']}")
            print(f"   Active zones:")
            for zone in info['zones'][:5]:  # Show first 5
                zone_name = zone.get('name', 'unknown')
                print(f"     - {zone_name}")
            if info['zone_count'] > 5:
                print(f"     ... and {info['zone_count'] - 5} more")
            print()
            return True
        else:
            print("❌ Connection failed")
            print()
            return False

connected = asyncio.run(test_connection())

if not connected:
    print("⚠️  Cannot connect to API. Check your token.")
    sys.exit(1)

# ============================================================================
# Step 3: Show Registered Platforms
# ============================================================================

print("🌐 Step 3: Registered Platform Scrapers")
print("-" * 80)

platforms = get_registered_platforms()
print(f"✅ {len(platforms)} platforms registered:")
for platform in platforms:
    print(f"   - {platform}")
print()

# ============================================================================
# Step 4: Test Generic Web Scraper (Web Unlocker)
# ============================================================================

print("🕷️  Step 4: Test Generic Web Scraper")
print("-" * 80)
print("Scraping https://httpbin.org/html (test URL)...")
print()

try:
    result = client.scrape.generic.url("https://httpbin.org/html")
    
    if result.success:
        print("✅ Generic scrape successful!")
        print(f"   URL: {result.url}")
        print(f"   Status: {result.status}")
        print(f"   Domain: {result.root_domain}")
        print(f"   Content size: {result.html_char_size:,} characters")
        print(f"   Elapsed time: {result.elapsed_ms():.2f}ms")
        print(f"   Data preview: {str(result.data)[:100]}...")
        print()
    else:
        print(f"❌ Generic scrape failed: {result.error}")
        print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()

# ============================================================================
# Step 5: Show Platform Scraper Interfaces
# ============================================================================

print("🎯 Step 5: Platform Scraper Interface Examples")
print("-" * 80)
print()

print("📦 Amazon Scraper:")
print("   Available methods:")
print(f"     - scrape(urls=[...])           - URL-based product scraping")
print(f"     - products(keyword='laptop')   - Keyword-based product search")
print(f"     - reviews(product_url='...')   - Get product reviews")
print()

amazon = client.scrape.amazon
print(f"   Instance: {amazon}")
print(f"   Dataset ID: {amazon.DATASET_ID}")
print()

print("💼 LinkedIn Scraper:")
print("   Available methods:")
print(f"     - scrape(urls=[...])                    - URL-based scraping")
print(f"     - profiles(keyword='data scientist')    - Search profiles")
print(f"     - companies(keyword='tech startup')     - Search companies")
print(f"     - jobs(keyword='python', location='NYC') - Search jobs")
print()

linkedin = client.scrape.linkedin
print(f"   Instance: {linkedin}")
print(f"   Datasets:")
print(f"     - Profiles: {linkedin.DATASET_ID}")
print(f"     - Companies: {linkedin.DATASET_ID_COMPANIES}")
print(f"     - Jobs: {linkedin.DATASET_ID_JOBS}")
print()

print("🤖 ChatGPT Scraper:")
print("   Available methods:")
print(f"     - prompt(prompt='Explain Python')       - Single prompt")
print(f"     - prompts(prompts=['Q1', 'Q2'])         - Batch prompts")
print()

chatgpt = client.scrape.chatgpt
print(f"   Instance: {chatgpt}")
print(f"   Dataset ID: {chatgpt.DATASET_ID}")
print()

# ============================================================================
# Step 6: Interactive Menu
# ============================================================================

print("🎮 Step 6: Interactive Testing Menu")
print("-" * 80)
print()
print("What would you like to test?")
print()
print("  1. Test generic scraping (httpbin.org)")
print("  2. Test Amazon product search (requires credits)")
print("  3. Test LinkedIn job search (requires credits)")
print("  4. Test ChatGPT prompt (requires credits)")
print("  5. Show full client interface")
print("  6. Exit")
print()

def test_generic_scrape():
    """Test generic web scraping."""
    url = input("Enter URL to scrape (or press Enter for httpbin.org/json): ").strip()
    url = url or "https://httpbin.org/json"
    
    print(f"\nScraping: {url}")
    result = client.scrape.generic.url(url)
    
    if result.success:
        print(f"✅ Success!")
        print(f"   Status: {result.status}")
        print(f"   Size: {result.html_char_size} chars")
        print(f"   Time: {result.elapsed_ms():.2f}ms")
        print(f"   Data preview: {str(result.data)[:200]}...")
    else:
        print(f"❌ Failed: {result.error}")

def test_amazon_products():
    """Test Amazon product search."""
    keyword = input("Enter search keyword (e.g., 'laptop'): ").strip()
    if not keyword:
        print("❌ Keyword required")
        return
    
    print(f"\nSearching Amazon for: {keyword}")
    print("⚠️  This will use Bright Data credits!")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled")
        return
    
    try:
        result = client.scrape.amazon.products(keyword=keyword, max_results=5)
        
        if result.success:
            print(f"✅ Success!")
            print(f"   Found {result.row_count} products")
            print(f"   Cost: ${result.cost:.4f}" if result.cost else "   Cost: N/A")
            print(f"   Time: {result.elapsed_ms():.2f}ms")
            
            if isinstance(result.data, list):
                for i, product in enumerate(result.data[:3], 1):
                    print(f"\n   Product {i}:")
                    print(f"     Title: {product.get('title', 'N/A')[:60]}")
                    print(f"     Price: {product.get('price', 'N/A')}")
        else:
            print(f"❌ Failed: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_linkedin_jobs():
    """Test LinkedIn job search."""
    keyword = input("Enter job keyword (e.g., 'python developer'): ").strip()
    location = input("Enter location (e.g., 'NYC'): ").strip()
    
    if not keyword:
        print("❌ Keyword required")
        return
    
    print(f"\nSearching LinkedIn jobs: {keyword}")
    if location:
        print(f"Location: {location}")
    print("⚠️  This will use Bright Data credits!")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled")
        return
    
    try:
        result = client.scrape.linkedin.jobs(
            keyword=keyword,
            location=location if location else None,
            max_results=5
        )
        
        if result.success:
            print(f"✅ Success!")
            print(f"   Found {result.row_count} jobs")
            print(f"   Cost: ${result.cost:.4f}" if result.cost else "   Cost: N/A")
        else:
            print(f"❌ Failed: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_chatgpt_prompt():
    """Test ChatGPT prompt."""
    prompt = input("Enter prompt for ChatGPT: ").strip()
    
    if not prompt:
        print("❌ Prompt required")
        return
    
    print(f"\nSending prompt to ChatGPT: {prompt}")
    print("⚠️  This will use Bright Data credits!")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled")
        return
    
    try:
        result = client.scrape.chatgpt.prompt(prompt=prompt)
        
        if result.success:
            print(f"✅ Success!")
            print(f"   Cost: ${result.cost:.4f}" if result.cost else "   Cost: N/A")
            print(f"   Response: {result.data}")
        else:
            print(f"❌ Failed: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_interface():
    """Show full client interface."""
    print("\n" + "=" * 80)
    print("📖 FULL CLIENT INTERFACE")
    print("=" * 80)
    print()
    
    print("Client Initialization:")
    print("  client = BrightDataClient()  # Auto-loads from env")
    print("  client = BrightDataClient(token='your_token')")
    print()
    
    print("Connection Management:")
    print("  is_valid = await client.test_connection()")
    print("  info = await client.get_account_info()")
    print()
    
    print("Generic Web Scraping (Web Unlocker):")
    print("  result = client.scrape.generic.url('https://example.com')")
    print("  result = await client.scrape.generic.url_async('https://example.com')")
    print()
    
    print("Amazon Scraper:")
    print("  # URL-based scraping")
    print("  result = client.scrape.amazon.scrape(urls=['https://amazon.com/dp/B123'])")
    print()
    print("  # Keyword-based search")
    print("  result = client.scrape.amazon.products(keyword='laptop', max_results=10)")
    print("  result = client.scrape.amazon.reviews(product_url='https://amazon.com/dp/B123')")
    print()
    
    print("LinkedIn Scraper:")
    print("  # URL-based scraping")
    print("  result = client.scrape.linkedin.scrape(urls=['https://linkedin.com/in/john'])")
    print()
    print("  # Keyword-based search")
    print("  result = client.scrape.linkedin.profiles(keyword='data scientist', location='SF')")
    print("  result = client.scrape.linkedin.companies(keyword='tech startup', location='NYC')")
    print("  result = client.scrape.linkedin.jobs(keyword='python', location='remote')")
    print()
    
    print("ChatGPT Scraper:")
    print("  result = client.scrape.chatgpt.prompt(prompt='Explain async programming')")
    print("  result = client.scrape.chatgpt.prompts(prompts=['Q1', 'Q2', 'Q3'])")
    print()
    
    print("Result Objects:")
    print("  result.success       # True/False")
    print("  result.data          # Scraped data")
    print("  result.elapsed_ms()  # Timing")
    print("  result.cost          # Cost in USD")
    print("  result.to_json()     # Serialize")
    print()

# Interactive menu
while True:
    try:
        choice = input("\nEnter choice (1-6): ").strip()
        print()
        
        if choice == "1":
            test_generic_scrape()
        elif choice == "2":
            test_amazon_products()
        elif choice == "3":
            test_linkedin_jobs()
        elif choice == "4":
            test_chatgpt_prompt()
        elif choice == "5":
            show_interface()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 80)
print("Demo completed!")
print("=" * 80)

