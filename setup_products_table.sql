-- PRODUCTS TABLE SETUP FOR KATYAYANI ORGANICS
-- Run this in your Supabase SQL Editor to create the products table

-- ============ PRODUCTS TABLE ============
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'INR',
    benefits TEXT,
    ingredients TEXT,
    usage_instructions TEXT,
    rating DECIMAL(3, 1),
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100) UNIQUE,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Create index on frequently searched columns
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);

-- Enable Row-Level Security (optional)
-- ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Grant permissions to anon user (for Supabase)
GRANT SELECT ON products TO anon;
GRANT INSERT, UPDATE, DELETE ON products TO authenticated;

-- Insert sample products for Katyayani Organics (optional - uncomment if needed)
/*
INSERT INTO products (name, description, category, price, benefits, rating) VALUES
('Organic Turmeric Powder', 'Pure organic turmeric with anti-inflammatory properties', 'Spices', 250.00, 'Anti-inflammatory, aids digestion, boosts immunity', 4.8),
('Cold-Pressed Coconut Oil', 'Virgin coconut oil for cooking and skincare', 'Oils', 450.00, 'Moisturizing, heart-healthy, chemical-free', 4.9),
('Organic Honey', 'Raw, unpasteurized organic honey from local bees', 'Condiments', 350.00, 'Energy boost, cough relief, natural sweetener', 4.7),
('Organic Ghee', 'Pure clarified butter made from organic cow milk', 'Dairy', 500.00, 'Aids digestion, improves immunity, rich in vitamins', 4.8);
*/

-- ============ SUCCESS ============
-- Products table has been created!
