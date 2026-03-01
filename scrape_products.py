"""
Katyayani Organics - Product Web Scraper
Fetches all product details from the Katyayani Organics website
and stores them in the database for Gemini AI chatbot

Features:
- Scrapes product name, price, description, image, category
- Stores products in Supabase database
- Handles pagination and multiple categories
- Error handling and logging
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import List, Dict, Any
import time
from datetime import datetime
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
WEBSITE_URL = "https://www.katyayaniorganics.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

class KatyayaniScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.products = []
        
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a page and return BeautifulSoup object"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def scrape_products_list(self, category_url: str = None) -> List[Dict]:
        """Scrape product listings from category page"""
        url = category_url or f"{WEBSITE_URL}/shop-2/"
        soup = self.fetch_page(url)
        
        if not soup:
            return []
        
        products = []
        
        # Try WooCommerce selectors first - li.product
        product_containers = soup.find_all('li', class_='product')
        
        if not product_containers:
            # Try div.product-item or div.product
            product_containers = soup.find_all('div', class_=['product-item', 'product', 'woocommerce-loop-product'])
        
        if not product_containers:
            # Try any div with data-product-id
            product_containers = soup.find_all('div', attrs={'data-product-id': True})
        
        logger.info(f"Found {len(product_containers)} product containers")
        
        for container in product_containers:
            try:
                product = self.extract_product_info(container)
                if product and product.get('name') != "Unknown":
                    products.append(product)
            except Exception as e:
                logger.error(f"Error extracting product info: {str(e)}")
                continue
        
        return products
    
    def extract_product_info(self, container) -> Dict[str, Any]:
        """Extract product information from a product container"""
        try:
            product = {}
            
            # Product name - try different selectors for WooCommerce
            name_elem = container.find(['h2', 'h3', 'a'], class_=['product-name', 'woocommerce-loop-product__title', 'product-title'])
            if not name_elem:
                # Try finding any link with product class
                name_elem = container.find('a', class_='woocommerce-LoopProduct-link')
            
            product['name'] = name_elem.text.strip() if name_elem else "Unknown"
            
            # Product link
            link_elem = container.find('a', href=True, class_='woocommerce-LoopProduct-link')
            if not link_elem:
                link_elem = container.find('a', href=True)
            product['url'] = urljoin(WEBSITE_URL, link_elem['href']) if link_elem else ""
            
            # Product price - WooCommerce uses span.woocommerce-Price-amount
            price_elem = container.find(['span', 'div'], class_=['price', 'woocommerce-Price-amount', 'amount'])
            if price_elem:
                price_text = price_elem.text.strip()
                # Extract numeric value
                import re
                price_match = re.search(r'[\d,]+(?:\.\d+)?', price_text.replace(',', ''))
                product['price'] = float(price_match.group()) if price_match else 0
                product['price_text'] = price_text
            else:
                product['price'] = 0
                product['price_text'] = "Price on request"
            
            # Product description
            desc_elem = container.find(['p', 'div'], class_=['description', 'summary', 'product-description'])
            product['description'] = desc_elem.text.strip() if desc_elem else ""
            
            # Product image
            img_elem = container.find('img', class_=['wp-post-image', 'product-image', 'woocommerce-placeholder'])
            if img_elem:
                product['image'] = img_elem.get('src') or img_elem.get('data-src') or ""
                if product['image']:
                    product['image'] = urljoin(WEBSITE_URL, product['image'])
            else:
                product['image'] = ""
            
            # Category - from breadcrumb or category class
            category_elem = container.find(['span', 'div'], class_=['category', 'cat-links', 'product-category'])
            product['category'] = category_elem.text.strip() if category_elem else "Agricultural Products"
            
            # Stock/Availability
            stock_elem = container.find(['span', 'p'], class_=['stock', 'in-stock', 'out-of-stock', 'availability'])
            if stock_elem:
                stock_text = stock_elem.text.strip()
                product['availability'] = "In Stock" if "in" in stock_text.lower() else "Out of Stock"
            else:
                product['availability'] = "In Stock"
            
            # Rating - try to find star rating
            rating_elem = container.find(['div', 'span'], class_=['rating', 'star-rating', 'woocommerce-rating'])
            if rating_elem:
                import re
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:out of|/)', rating_text)
                product['rating'] = float(rating_match.group(1)) if rating_match else 0
            else:
                product['rating'] = 0
            
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product info: {str(e)}")
            return None
    
    def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """Scrape detailed information from individual product page"""
        soup = self.fetch_page(product_url)
        if not soup:
            return {}
        
        details = {}
        
        try:
            # Additional details from product page
            specs_elem = soup.find(['div', 'section'], class_=['specifications', 'product-details', 'specs'])
            if specs_elem:
                details['specifications'] = specs_elem.text.strip()
            
            # Benefits/Features
            benefits_elem = soup.find(['div', 'section'], class_=['benefits', 'features'])
            if benefits_elem:
                details['benefits'] = benefits_elem.text.strip()
            
            # Ingredients
            ingredients_elem = soup.find(['div', 'section'], class_=['ingredients'])
            if ingredients_elem:
                details['ingredients'] = ingredients_elem.text.strip()
            
            # Reviews/Rating
            rating_elem = soup.find(['div', 'span'], class_=['rating', 'star-rating'])
            if rating_elem:
                import re
                rating_match = re.search(r'[\d.]+', rating_elem.text)
                details['rating'] = float(rating_match.group()) if rating_match else 0
            
        except Exception as e:
            logger.error(f"Error scraping product details from {product_url}: {str(e)}")
        
        return details
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from website"""
        logger.info("Starting Katyayani Organics product scraping...")
        
        # Scrape products from main shop and category pages
        pages_to_scrape = [
            f"{WEBSITE_URL}/shop-2/",  # Main shop page
            f"{WEBSITE_URL}/product-category/all-products/fertilizers-soil/",  # Fertilizers
            f"{WEBSITE_URL}/product-category/all-products/pest-control/",  # Pesticides
            f"{WEBSITE_URL}/product-category/all-products/fungicides-weedicides/",  # Fungicides
        ]
        
        all_products = []
        
        for page_url in pages_to_scrape:
            logger.info(f"\n📍 Scraping: {page_url}")
            try:
                time.sleep(2)  # Be respectful
                products = self.scrape_products_list(page_url)
                all_products.extend(products)
                logger.info(f"✅ Found {len(products)} products from this page")
            except Exception as e:
                logger.error(f"Error scraping {page_url}: {str(e)}")
                continue
        
        # Remove duplicates based on product name
        unique_products = {}
        for product in all_products:
            name = product.get('name', '')
            if name and name not in unique_products:
                unique_products[name] = product
        
        self.products = list(unique_products.values())
        logger.info(f"\n✅ Scraping complete. Total unique products: {len(self.products)}")
        return self.products
    
    def save_to_json(self, filename: str = "products.json"):
        """Save products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            logger.info(f"Products saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")


# Supabase Integration
def save_products_to_supabase(products: List[Dict]):
    """Save scraped products to Supabase database"""
    try:
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        import supabase
        
        # Initialize Supabase client
        client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        logger.info("Saving products to Supabase...")
        
        for product in products:
            # Prepare product data
            product_data = {
                'name': product.get('name'),
                'price': product.get('price'),
                'description': product.get('description'),
                'image_url': product.get('image'),
                'category': product.get('category'),
                'availability': product.get('availability'),
                'url': product.get('url'),
                'specifications': product.get('specifications', ''),
                'benefits': product.get('benefits', ''),
                'ingredients': product.get('ingredients', ''),
                'rating': product.get('rating', 0),
                'scraped_at': datetime.now().isoformat(),
            }
            
            try:
                # Upsert product (update if exists, insert if not)
                response = client.table('products').upsert(product_data).execute()
                logger.info(f"Saved product: {product.get('name')}")
            except Exception as e:
                logger.error(f"Error saving {product.get('name')}: {str(e)}")
        
        logger.info("All products saved to Supabase!")
        
    except ImportError:
        logger.error("Supabase client not installed. Install with: pip install supabase")
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")


# Database Schema Creation (SQL for Supabase)
CREATE_PRODUCTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2),
    description TEXT,
    image_url VARCHAR(500),
    category VARCHAR(100),
    availability VARCHAR(50),
    url VARCHAR(500),
    specifications TEXT,
    benefits TEXT,
    ingredients TEXT,
    rating DECIMAL(3, 2),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
"""


def main():
    """Main execution"""
    import sys
    
    logger.info("=" * 60)
    logger.info("KATYAYANI ORGANICS - PRODUCT SCRAPER")
    logger.info("=" * 60)
    
    # Initialize scraper
    scraper = KatyayaniScraper()
    
    # Scrape products
    try:
        products = scraper.get_all_products()
        scraper.products = products
        
        # Save to JSON
        scraper.save_to_json('katyayani_products.json')
        
        # Save to Supabase (optional)
        if len(products) > 0:
            should_save = input("\nSave products to Supabase? (y/n): ").lower() == 'y'
            if should_save:
                save_products_to_supabase(products)
        
        # Display summary
        print("\n" + "=" * 60)
        print(f"✅ SCRAPING COMPLETE")
        print(f"Total Products Scraped: {len(products)}")
        if products:
            print(f"\nSample Product:")
            sample = products[0]
            print(f"  Name: {sample.get('name')}")
            print(f"  Price: ₹{sample.get('price')}")
            print(f"  Category: {sample.get('category')}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
