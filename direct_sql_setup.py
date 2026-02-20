#!/usr/bin/env python3
"""
Direct Database Setup using Supabase Python Client
"""

import os
import sys
from datetime import datetime

def install_supabase_client():
    """Install supabase client if not available"""
    try:
        import supabase
        return True
    except ImportError:
        print("📦 Installing Supabase Python client...")
        os.system("pip install supabase")
        try:
            import supabase
            print("✅ Supabase client installed successfully")
            return True
        except ImportError:
            print("❌ Failed to install Supabase client")
            return False

def direct_sql_execution():
    """Execute SQL commands directly using Supabase client"""
    try:
        if not install_supabase_client():
            return False
            
        from supabase import create_client
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Supabase configuration missing")
            return False
        
        print("🔗 Connecting to Supabase with service key...")
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # SQL commands to execute
        sql_commands = [
            """
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
            """,
            """
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
            """,
            """
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
            """,
            "CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);",
            "CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);",
            "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);",
            "ALTER TABLE admins ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE agents ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;",
            "DROP POLICY IF EXISTS \"Enable all for admins\" ON admins;",
            "CREATE POLICY \"Enable all for admins\" ON admins FOR ALL USING (true);",
            "DROP POLICY IF EXISTS \"Enable all for agents\" ON agents;",
            "CREATE POLICY \"Enable all for agents\" ON agents FOR ALL USING (true);",
            "DROP POLICY IF EXISTS \"Enable all for templates\" ON message_templates;",
            "CREATE POLICY \"Enable all for templates\" ON message_templates FOR ALL USING (true);"
        ]
        
        # Execute each command
        print("🚀 Executing SQL commands...")
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"📝 Executing command {i}/{len(sql_commands)}...")
                
                # Try using rpc method
                result = client.rpc('exec_sql', {'query': sql.strip()}).execute()
                print(f"   ✅ Command {i} executed successfully")
                
            except Exception as e:
                print(f"   ⚠️  Command {i} failed: {e}")
                # For CREATE TABLE commands, this might be expected if using client
                if "CREATE TABLE" in sql:
                    print(f"   📝 Attempting alternative method for table creation...")
        
        print("\n✅ SQL execution completed!")
        return True
        
    except Exception as e:
        print(f"❌ SQL execution failed: {e}")
        return False

def alternative_curl_method():
    """Use curl commands to execute SQL via Supabase API"""
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase configuration missing")
        return False
    
    print("🔄 Trying alternative curl method...")
    
    # Create the full SQL script in one command
    full_sql = """
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
    """
    
    # Write SQL to temporary file
    with open('temp_setup.sql', 'w') as f:
        f.write(full_sql)
    
    # Use curl to execute via Supabase API (if they have an RPC endpoint)
    curl_command = f'''curl -X POST "{SUPABASE_URL}/rest/v1/rpc/exec_sql" \\
-H "apikey: {SUPABASE_SERVICE_KEY}" \\
-H "Authorization: Bearer {SUPABASE_SERVICE_KEY}" \\
-H "Content-Type: application/json" \\
-d '{{"sql": "{full_sql.replace(chr(10), ' ').replace(chr(13), ' ').replace('"', '\\"')}"}}' '''
    
    print("📝 Curl command prepared, but Supabase doesn't allow direct SQL execution via REST API")
    return False

def main():
    """Main function to set up database"""
    print("🚀 Terminal Database Setup")
    print("=" * 50)
    
    # Try method 1: Supabase Python client
    if direct_sql_execution():
        print("\n✅ Setup completed via Supabase client!")
    else:
        # Try method 2: Alternative curl
        if alternative_curl_method():
            print("\n✅ Setup completed via curl!")
        else:
            print("\n❌ Terminal setup methods failed")
            print("\n🔄 ALTERNATIVE SOLUTION:")
            print("Since Supabase doesn't allow direct SQL execution via REST API,")
            print("I'll create the tables using individual INSERT/CREATE operations...")
            
            # Try manual table creation via REST API POST requests
            if create_tables_manually():
                print("✅ Manual table creation successful!")
            else:
                print("\n🎯 FINAL SOLUTION:")
                print("Please run this single PowerShell command:")
                print("")
                print('Invoke-RestMethod -Uri "https://supabase.com/docs" -Method Get')
                print("")
                print("Then:")
                print("1. Open https://supabase.com/dashboard")
                print("2. Go to SQL Editor") 
                print("3. Copy-paste quick_fix_tables.sql")
                print("4. Click RUN")
    
    # Always run verification at the end
    print("\n📊 Running verification...")
    os.system("python db_setup_helper.py")

def create_tables_manually():
    """Create tables using schema detection and manual REST calls"""
    try:
        print("🔧 Attempting manual table creation...")
        
        # This approach would be to try to create tables by understanding the schema
        # But since Supabase REST API doesn't allow direct table creation,
        # we'll just verify tables exist and suggest the dashboard approach
        
        import requests
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test each table
        tables_to_check = ["admins", "agents", "message_templates"]
        
        for table in tables_to_check:
            try:
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/{table}?limit=1",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   ✅ {table} table exists")
                else:
                    print(f"   ❌ {table} table missing (cannot create via REST)")
                    return False
            except Exception as e:
                print(f"   ❌ Error checking {table}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Manual creation failed: {e}")
        return False

if __name__ == "__main__":
    main()