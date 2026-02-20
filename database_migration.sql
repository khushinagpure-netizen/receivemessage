-- Database Migration Script for Enhanced Features
-- Add fields to support message status tracking, media, and sentiment analysis
-- Run this in your Supabase SQL Editor

-- ============ CONVERSATIONS TABLE ENHANCEMENTS ============

-- Add fields to conversations table if they don't exist
ALTER TABLE IF EXISTS conversations
ADD COLUMN IF NOT EXISTS sentiment VARCHAR(50); -- 'positive', 'negative', 'neutral', 'mixed'

ALTER TABLE IF EXISTS conversations
ADD COLUMN IF NOT EXISTS sentiment_last_updated TIMESTAMP;

ALTER TABLE IF EXISTS conversations
ADD COLUMN IF NOT EXISTS media_count INT DEFAULT 0;

-- ============ MESSAGES TABLE ENHANCEMENTS ============

-- Add message_id field if not exists
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS message_id VARCHAR(255); -- WhatsApp message ID

-- Add media_url for direct media storage
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS media_url TEXT;

-- Add sentiment field
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS sentiment VARCHAR(50); -- 'positive', 'negative', 'neutral', 'mixed'

-- Add sentiment_confidence
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS sentiment_confidence FLOAT DEFAULT 0.0;

-- Add direction field
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS direction VARCHAR(50); -- 'inbound', 'outbound'

-- Add error tracking
ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);

ALTER TABLE IF EXISTS messages
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- ============ CREATE SENTIMENT TRACKING TABLE ============

CREATE TABLE IF NOT EXISTS sentiment_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    message_id UUID REFERENCES messages(id),
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ CREATE INDEXES FOR PERFORMANCE ============

-- Index for message queries
CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_message_id ON messages(message_id);

-- Index for sentiment tracking
CREATE INDEX IF NOT EXISTS idx_sentiment_tracking_phone ON sentiment_tracking(phone);
CREATE INDEX IF NOT EXISTS idx_sentiment_tracking_created_at ON sentiment_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_tracking_sentiment ON sentiment_tracking(sentiment);

-- Index for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone);
CREATE INDEX IF NOT EXISTS idx_conversations_sentiment ON conversations(sentiment);

-- ============ VIEWS FOR ANALYTICS ============

-- View for message statistics
CREATE OR REPLACE VIEW IF EXISTS message_stats_view AS
SELECT 
    phone,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as sent_messages,
    COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as received_messages,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN status IN ('read', 'seen') THEN 1 END) as read_messages,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_messages,
    AVG(CASE WHEN sentiment = 'positive' THEN 1 WHEN sentiment = 'negative' THEN 0 ELSE 0.5 END) as average_sentiment
FROM messages
GROUP BY phone;

-- View for recent activity
CREATE OR REPLACE VIEW IF EXISTS recent_activity_view AS
SELECT 
    m.id,
    m.phone,
    m.message,
    m.direction,
    m.status,
    m.sentiment,
    m.created_at,
    l.name,
    l.email
FROM messages m
LEFT JOIN leads l ON m.lead_id = l.id
WHERE m.created_at > NOW() - INTERVAL '7 days'
ORDER BY m.created_at DESC;

-- ============ NOTES ============
-- After running this migration:
-- 1. Update any application code that references old message fields
-- 2. Test sentiment analysis on existing conversations
-- 3. Create backups before migration
-- 4. Monitor performance with new indexes
