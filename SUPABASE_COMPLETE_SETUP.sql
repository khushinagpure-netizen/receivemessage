-- Complete Supabase Database Setup for Multi-Channel Communication API
-- Run this in your Supabase SQL Editor to create all required tables and views

-- ============ DROP EXISTING TABLES (CAUTION!) ============
-- Uncomment only if you want to reset and start fresh
-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS conversations CASCADE;
-- DROP TABLE IF EXISTS leads CASCADE;
-- DROP TABLE IF EXISTS api_logs CASCADE;
-- DROP TABLE IF EXISTS sentiment_tracking CASCADE;

-- ============ LEADS TABLE ============

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'follow-up', 'won', 'lost'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ CONVERSATIONS TABLE ============

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    message TEXT,
    sender VARCHAR(255),
    direction VARCHAR(50), -- 'inbound', 'outbound'
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'seen', 'failed', 'received'
    sentiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ MESSAGES TABLE ============

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    message TEXT,
    direction VARCHAR(50), -- 'inbound', 'outbound'
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'seen', 'failed'
    message_id VARCHAR(255),
    sender_name VARCHAR(255),
    media_url TEXT,
    sentiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ API LOGS TABLE ============

CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(255),
    method VARCHAR(50),
    phone VARCHAR(20),
    status_code INT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ SENTIMENT TRACKING TABLE ============

CREATE TABLE IF NOT EXISTS sentiment_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    message_id UUID,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ CREATE INDEXES FOR PERFORMANCE ============

CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_direction ON conversations(direction);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

CREATE INDEX IF NOT EXISTS idx_sentiment_tracking_phone ON sentiment_tracking(phone);
CREATE INDEX IF NOT EXISTS idx_sentiment_tracking_created_at ON sentiment_tracking(created_at);

CREATE INDEX IF NOT EXISTS idx_api_logs_phone ON api_logs(phone);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);

-- ============ CREATE VIEWS FOR ANALYTICS ============

-- View: Message Statistics by Phone
CREATE OR REPLACE VIEW message_stats_view AS
SELECT 
    COALESCE(m.phone, c.phone) as phone,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(CASE WHEN m.direction = 'outbound' THEN 1 END) as sent_messages,
    COUNT(CASE WHEN m.direction = 'inbound' THEN 1 END) as received_messages,
    COUNT(CASE WHEN m.status = 'delivered' THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN m.status IN ('read', 'seen') THEN 1 END) as read_messages,
    COUNT(CASE WHEN m.status = 'failed' THEN 1 END) as failed_messages,
    ROUND(
        COUNT(CASE WHEN m.status IN ('delivered', 'read', 'seen') THEN 1 END)::numeric / 
        NULLIF(COUNT(CASE WHEN m.direction = 'outbound' THEN 1 END), 0) * 100, 
        2
    ) as delivery_rate_percent,
    ROUND(
        COUNT(CASE WHEN m.direction = 'outbound' AND m.status IN ('read', 'seen') THEN 1 END)::numeric / 
        NULLIF(COUNT(CASE WHEN m.direction = 'outbound' THEN 1 END), 0) * 100, 
        2
    ) as read_rate_percent,
    MAX(COALESCE(m.created_at, c.created_at)) as last_activity
FROM messages m
FULL OUTER JOIN conversations c ON m.phone = c.phone
GROUP BY COALESCE(m.phone, c.phone);

-- View: Conversation Statistics
CREATE OR REPLACE VIEW conversation_stats_view AS
SELECT 
    phone,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as sent_messages,
    COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as received_messages,
    COUNT(CASE WHEN status IN ('delivered', 'read', 'seen') THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN status IN ('read', 'seen') THEN 1 END) as read_messages,
    MAX(created_at) as last_message_at
FROM conversations
GROUP BY phone;

-- View: Recent Messages
CREATE OR REPLACE VIEW recent_messages_view AS
SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY phone ORDER BY created_at DESC) as row_num
FROM messages
WHERE created_at > NOW() - INTERVAL '30 days'
ORDER BY created_at DESC;

-- View: Lead Activity
CREATE OR REPLACE VIEW lead_activity_view AS
SELECT 
    l.id,
    l.phone,
    l.name,
    l.status,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(CASE WHEN c.direction = 'inbound' THEN 1 END) as messages_received,
    COUNT(CASE WHEN c.direction = 'outbound' THEN 1 END) as messages_sent,
    MAX(c.created_at) as last_contact,
    l.created_at as lead_created_at
FROM leads l
LEFT JOIN conversations c ON l.id = c.lead_id
GROUP BY l.id, l.phone, l.name, l.status, l.created_at;

-- ============ ENABLE ROW-LEVEL SECURITY (RLS) ============
-- Optional: Enable RLS for production use

-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sentiment_tracking ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE api_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (for development)
-- CREATE POLICY "Enable read access for all users" ON leads FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for all users" ON leads FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable update for all users" ON leads FOR UPDATE USING (true);

-- ============ GRANT PERMISSIONS ============
-- Ensure proper permissions for Supabase Anon Key user

GRANT SELECT, INSERT, UPDATE, DELETE ON leads TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON messages TO anon;
GRANT SELECT, INSERT ON api_logs TO anon;
GRANT SELECT, INSERT ON sentiment_tracking TO anon;

GRANT SELECT ON message_stats_view TO anon;
GRANT SELECT ON conversation_stats_view TO anon;
GRANT SELECT ON recent_messages_view TO anon;
GRANT SELECT ON lead_activity_view TO anon;

-- ============ SUCCESS ============
-- All tables, indexes, and views have been created!
-- Your Supabase database is now ready for the Multi-Channel Communication API
