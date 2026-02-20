-- Complete Supabase Setup with Real-Time Features
-- Run this in your Supabase SQL Editor

-- ============ DROP OLD CONSTRAINTS ============
ALTER TABLE IF EXISTS messages DROP CONSTRAINT IF EXISTS messages_pkey CASCADE;
ALTER TABLE IF EXISTS conversations DROP CONSTRAINT IF EXISTS conversations_pkey CASCADE;
ALTER TABLE IF EXISTS leads DROP CONSTRAINT IF EXISTS leads_pkey CASCADE;

-- ============ LEADS TABLE ============
DROP TABLE IF EXISTS leads CASCADE;

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'follow-up', 'won', 'lost'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ MESSAGES TABLE - PRIMARY TABLE FOR SENDING/RECEIVING ============
DROP TABLE IF EXISTS messages CASCADE;

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    direction VARCHAR(50) NOT NULL, -- 'inbound', 'outbound'
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'seen', 'failed', 'pending', 'received'
    message_id VARCHAR(255) UNIQUE,
    sender_name VARCHAR(255),
    sender_type VARCHAR(50) DEFAULT 'customer', -- 'customer', 'agent', 'system'
    media_url TEXT,
    media_type VARCHAR(50), -- 'image', 'video', 'document', 'audio', 'file'
    caption TEXT,
    sentiment VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ CONVERSATIONS TABLE - GROUPED BY THREAD ============
DROP TABLE IF EXISTS conversations CASCADE;

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    sender VARCHAR(255),
    sender_type VARCHAR(50) DEFAULT 'customer', -- 'customer', 'agent', 'system'
    direction VARCHAR(50) NOT NULL, -- 'inbound', 'outbound'
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'seen', 'failed', 'received'
    sentiment VARCHAR(50),
    message_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ API LOGS TABLE ============
DROP TABLE IF EXISTS api_logs CASCADE;

CREATE TABLE api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    status_code INT,
    response_time_ms INT,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ TEMPLATES TABLE ============
DROP TABLE IF EXISTS templates CASCADE;

CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'APPROVED', 'REJECTED'
    language VARCHAR(10) DEFAULT 'en_US',
    body TEXT NOT NULL,
    footer TEXT,
    header_type VARCHAR(50), -- 'TEXT', 'IMAGE', 'VIDEO', 'DOCUMENT'
    header_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ SENTIMENT TRACKING TABLE ============
DROP TABLE IF EXISTS sentiment_tracking CASCADE;

CREATE TABLE sentiment_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    sentiment VARCHAR(50) NOT NULL, -- 'positive', 'negative', 'neutral', 'mixed'
    confidence FLOAT DEFAULT 0.0,
    message_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============ CREATE INDEXES FOR PERFORMANCE ============

-- Messages Indexes
CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_phone_created ON messages(phone, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_message_id ON messages(message_id);

-- Conversations Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_direction ON conversations(direction);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);

-- Leads Indexes
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

-- Sentiment Indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_phone ON sentiment_tracking(phone);
CREATE INDEX IF NOT EXISTS idx_sentiment_created_at ON sentiment_tracking(created_at DESC);

-- API Logs Indexes
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at DESC);

-- ============ ENABLE REALTIME FOR TABLES ============
-- These tables will automatically send realtime updates to subscribed clients

ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE leads;

-- ============ GRANT PERMISSIONS TO ANON USER ============
-- This allows your API to read/write data

GRANT SELECT, INSERT, UPDATE, DELETE ON messages TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON leads TO authenticated;
GRANT SELECT ON sentiment_tracking TO authenticated;
GRANT INSERT ON api_logs TO authenticated;
GRANT SELECT, INSERT, UPDATE ON templates TO authenticated;

-- ============ CREATE VIEWS FOR ANALYTICS ============

CREATE OR REPLACE VIEW message_stats AS
SELECT 
    phone,
    COUNT(*) as total_messages,
    SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as total_sent,
    SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as total_received,
    SUM(CASE WHEN status IN ('delivered', 'read', 'seen') THEN 1 ELSE 0 END) as delivered_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    MAX(created_at) as last_message_at
FROM messages
GROUP BY phone;

CREATE OR REPLACE VIEW conversation_summary AS
SELECT 
    c.phone,
    COUNT(DISTINCT c.id) as message_count,
    COUNT(DISTINCT c.lead_id) as unique_leads,
    MAX(c.created_at) as last_updated
FROM conversations c
GROUP BY c.phone;

-- ============ UPDATE TIMESTAMP TRIGGER ============
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
DROP TRIGGER IF EXISTS update_leads_timestamp ON leads;
CREATE TRIGGER update_leads_timestamp BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_messages_timestamp ON messages;
CREATE TRIGGER update_messages_timestamp BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conversations_timestamp ON conversations;
CREATE TRIGGER update_conversations_timestamp BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============ TEST DATA (OPTIONAL) ============
-- Uncomment to insert test data

-- INSERT INTO leads (phone, name, status) VALUES
-- ('917974734809', 'Test User 1', 'new'),
-- ('919876543210', 'Test User 2', 'contacted')
-- ON CONFLICT (phone) DO NOTHING;

-- INSERT INTO messages (phone, message, direction, status, sender_name, sender_type) VALUES
-- ('917974734809', 'Hello! This is a test message', 'inbound', 'received', 'Test User 1', 'customer'),
-- ('917974734809', 'Thanks for reaching out! How can we help?', 'outbound', 'sent', 'Agent', 'agent')
-- ON CONFLICT (message_id) DO NOTHING;

COMMIT;
