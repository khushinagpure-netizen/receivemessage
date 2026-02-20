-- QUICK FIX: Create only the missing critical tables
-- Run this in Supabase SQL Editor to fix admin/agent errors

-- Create admins table (MISSING - CRITICAL)
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(500),
    role VARCHAR(50) DEFAULT 'admin',
    status VARCHAR(50) DEFAULT 'active',
    permissions JSONB DEFAULT '{"all": true}',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create agents table (MISSING - CRITICAL) 
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(500),
    role VARCHAR(50) DEFAULT 'agent',
    status VARCHAR(50) DEFAULT 'active',
    assigned_leads_limit INT DEFAULT 50,
    current_leads_count INT DEFAULT 0,
    is_available BOOLEAN DEFAULT true,
    last_activity TIMESTAMP,
    performance_rating DECIMAL(3,2) DEFAULT 0.00,
    total_leads_handled INT DEFAULT 0,
    total_conversations INT DEFAULT 0,
    created_by UUID REFERENCES admins(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create message_templates table (MISSING - CRITICAL)
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255),
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    category VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_by_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_message_templates_name ON message_templates(name);

-- Enable Row Level Security
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;

-- Basic RLS Policies (permissive for now)
CREATE POLICY "Enable all for admins" ON admins FOR ALL USING (true);
CREATE POLICY "Enable all for agents" ON agents FOR ALL USING (true);
CREATE POLICY "Enable all for templates" ON message_templates FOR ALL USING (true);

-- Success message
SELECT '✅ CRITICAL TABLES CREATED! Admin/Agent endpoints will now work!' as status;