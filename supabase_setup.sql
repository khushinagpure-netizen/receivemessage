-- Supabase Database Setup Script
-- Run this in your Supabase SQL Editor to create all required tables

-- ============ TEAM & AGENTS ============

-- Create agents/team members table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(500),
    role VARCHAR(50) DEFAULT 'agent', -- 'admin', 'supervisor', 'agent'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'on_leave'
    assigned_leads_limit INT DEFAULT 50,
    current_leads_count INT DEFAULT 0,
    is_available BOOLEAN DEFAULT true,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create lead tags for segmentation
CREATE TABLE IF NOT EXISTS lead_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(10),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create leads table (enhanced)
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    country_code VARCHAR(5),
    source VARCHAR(100), -- 'whatsapp', 'sms', 'api', 'import', 'campaign'
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'follow-up', 'won', 'lost', 'unqualified'
    priority VARCHAR(20) DEFAULT 'medium', -- 'high', 'medium', 'low'
    assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    previous_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    last_contact_at TIMESTAMP,
    opt_in BOOLEAN DEFAULT false,
    opt_in_timestamp TIMESTAMP,
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create lead tags mapping
CREATE TABLE IF NOT EXISTS lead_lead_tags (
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES lead_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lead_id, tag_id)
);

-- Create lead status history for tracking status changes
CREATE TABLE IF NOT EXISTS lead_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by_agent_id UUID REFERENCES agents(id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ CONVERSATIONS & MESSAGES ============

-- Create conversations table (enhanced)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    phone VARCHAR(20) NOT NULL,
    channel VARCHAR(50) DEFAULT 'whatsapp', -- 'whatsapp', 'sms', 'call'
    is_active BOOLEAN DEFAULT true,
    message_count INT DEFAULT 0,
    last_message_at TIMESTAMP,
    is_archived BOOLEAN DEFAULT false,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create media table  
CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_id VARCHAR(255) NOT NULL UNIQUE, -- Meta's media_id or custom
    media_type VARCHAR(50) NOT NULL, -- 'image', 'video', 'document', 'audio'
    url VARCHAR(500),
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    uploader_agent_id UUID REFERENCES agents(id),
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table (enhanced)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    content TEXT,
    message_type VARCHAR(50) DEFAULT 'text', -- 'text', 'image', 'video', 'document', 'audio', 'interactive', 'template'
    channel VARCHAR(50) DEFAULT 'whatsapp',
    sender_type VARCHAR(50) NOT NULL, -- 'lead', 'agent', 'system'
    sender_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'failed'
    media_id UUID REFERENCES media(id),
    external_message_id VARCHAR(255), -- WhatsApp message ID
    metadata JSONB DEFAULT '{}', -- buttons, quick_replies, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create message status tracking
CREATE TABLE IF NOT EXISTS message_status_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- 'sent', 'delivered', 'read', 'failed'
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ AUTOMATION & SCHEDULING ============

-- Create automation rules  
CREATE TABLE IF NOT EXISTS automation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100), -- 'new_lead', 'keyword', 'time_based', 'status_change', 'missed_message'
    trigger_conditions JSONB NOT NULL, -- e.g., {"keywords": ["hello", "hi"]}
    action_type VARCHAR(100), -- 'send_message', 'assign_agent', 'change_status', 'send_template'
    action_data JSONB NOT NULL, 
    is_active BOOLEAN DEFAULT true,
    created_by_agent_id UUID NOT NULL REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create keyword triggers
CREATE TABLE IF NOT EXISTS keyword_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES automation_rules(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    response_template_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create scheduled messages
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_content TEXT NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    message_type VARCHAR(50) DEFAULT 'text',
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'sent', 'failed', 'cancelled'
    created_by_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ BROADCAST & CAMPAIGNS ============

-- Create broadcast campaigns
CREATE TABLE IF NOT EXISTS broadcast_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id UUID,
    message_content TEXT,
    target_tags JSONB DEFAULT '[]',
    filters JSONB DEFAULT '{}',
    scheduled_for TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft', 
    total_leads INT DEFAULT 0,
    sent_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    created_by_agent_id UUID NOT NULL REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create broadcast campaign recipients
CREATE TABLE IF NOT EXISTS broadcast_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES broadcast_campaigns(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending', 
    sent_at TIMESTAMP,
    message_id UUID REFERENCES messages(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ ANALYTICS & PERFORMANCE ============

-- Create agent performance metrics
CREATE TABLE IF NOT EXISTS agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    leads_handled INT DEFAULT 0,
    messages_sent INT DEFAULT 0,
    avg_response_time_seconds INT,
    total_interactions INT DEFAULT 0,
    conversion_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, date)
);

-- Create consent and opt-in logs
CREATE TABLE IF NOT EXISTS consent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method VARCHAR(100), 
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- ============ SECURITY & AUTHENTICATION ============

-- Create JWT tokens log
CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    token_hash VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ EXISTING ENHANCED TABLES ============

-- Create conversations table (keep old one for backward compatibility, but use new one above)
-- CREATE TABLE IF NOT EXISTS conversations (...)

-- Create messages table (keep old one for backward compatibility)
-- CREATE TABLE IF NOT EXISTS messages (...)

-- Create SMS messages table
CREATE TABLE IF NOT EXISTS sms_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    direction VARCHAR(20) NOT NULL, 
    status VARCHAR(50) DEFAULT 'pending',
    provider VARCHAR(100), 
    external_message_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create calls table
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    phone_number VARCHAR(20) NOT NULL,
    call_direction VARCHAR(20) NOT NULL, 
    call_status VARCHAR(50) NOT NULL, 
    duration_seconds INT DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    recording_url VARCHAR(255),
    call_notes TEXT,
    answered BOOLEAN DEFAULT false,
    provider VARCHAR(100),
    external_call_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create call recordings table
CREATE TABLE IF NOT EXISTS call_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    recording_url VARCHAR(500),
    duration_seconds INT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    transcription TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create call transcriptions table
CREATE TABLE IF NOT EXISTS call_transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    transcript TEXT,
    duration_seconds INT,
    language VARCHAR(10) DEFAULT 'en',
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create message templates table
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255),
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]', -- Array of variable names {var_name}
    category VARCHAR(100), -- 'greeting', 'support', 'promotion', 'follow-up'
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_by_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create API logs table (for tracking all API usage)
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL, -- 'GET', 'POST', 'PUT', 'DELETE'
    status_code INT,
    phone_number VARCHAR(20),
    agent_id UUID REFERENCES agents(id),
    request_body JSONB,
    response_body JSONB,
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============ INDEXES FOR PERFORMANCE ============

CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_lead_tags_name ON lead_tags(name);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_agent ON leads(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lead_status_history_lead_id ON lead_status_history(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone);
CREATE INDEX IF NOT EXISTS idx_conversations_channel ON conversations(channel);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(is_active);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_lead_id ON messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_status_tracking_message_id ON message_status_tracking(message_id);
CREATE INDEX IF NOT EXISTS idx_automation_rules_active ON automation_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_keyword_triggers_keyword ON keyword_triggers(keyword);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_lead_id ON scheduled_messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_scheduled_for ON scheduled_messages(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_broadcast_campaigns_status ON broadcast_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_campaign_id ON broadcast_recipients(campaign_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_recipients_lead_id ON broadcast_recipients(lead_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_id ON agent_performance(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_date ON agent_performance(date);
CREATE INDEX IF NOT EXISTS idx_consent_logs_lead_id ON consent_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_sms_messages_phone ON sms_messages(phone_number);
CREATE INDEX IF NOT EXISTS idx_sms_messages_status ON sms_messages(status);
CREATE INDEX IF NOT EXISTS idx_calls_lead_id ON calls(lead_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_id ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_phone ON calls(phone_number);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(call_status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_logs_agent_id ON api_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at DESC);

-- ============ ROW LEVEL SECURITY ============

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE broadcast_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_logs ENABLE ROW LEVEL SECURITY;

-- Basic RLS Policies
CREATE POLICY "Enable read for all users" ON agents FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated" ON agents FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable read leads" ON leads FOR SELECT USING (true);
CREATE POLICY "Enable insert leads" ON leads FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON leads
    FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON conversations
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON conversations
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable read access for all users" ON messages
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON messages
    FOR INSERT WITH CHECK (true);

-- Print summary
SELECT '✅ Tables created successfully!' as status;
