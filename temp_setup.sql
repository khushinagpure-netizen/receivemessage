
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
        created_by UUID,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS message_templates (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL UNIQUE,
        title VARCHAR(255),
        content TEXT NOT NULL,
        variables JSONB DEFAULT '[]',
        category VARCHAR(100),
        language VARCHAR(10) DEFAULT 'en',
        is_active BOOLEAN DEFAULT true,
        created_by_agent_id UUID,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
    ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;
    
    DROP POLICY IF EXISTS "Enable all for admins" ON admins;
    CREATE POLICY "Enable all for admins" ON admins FOR ALL USING (true);
    DROP POLICY IF EXISTS "Enable all for agents" ON agents;
    CREATE POLICY "Enable all for agents" ON agents FOR ALL USING (true);
    DROP POLICY IF EXISTS "Enable all for templates" ON message_templates;
    CREATE POLICY "Enable all for templates" ON message_templates FOR ALL USING (true);
    
    SELECT 'Database setup completed successfully!' as result;
    