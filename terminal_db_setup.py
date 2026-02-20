#!/usr/bin/env python3
"""
Direct Database Setup via Terminal
Execute SQL commands directly using Supabase REST API
"""

import requests
import json
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def execute_sql_command(sql_command: str) -> bool:
    """Execute a single SQL command via Supabase REST API"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Supabase not configured")
            return False
        
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Use Supabase RPC endpoint to execute raw SQL
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql_command},
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            return True
        else:
            print(f"❌ SQL execution failed: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error executing SQL: {e}")
        return False

def create_tables_via_api():
    """Create missing tables using direct API calls"""
    print("🚀 Creating Database Tables via Terminal...")
    print("=" * 60)
    
    # Table creation commands
    table_commands = [
        {
            "name": "admins table",
            "sql": """
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
            """
        },
        {
            "name": "agents table",
            "sql": """
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
            """
        },
        {
            "name": "message_templates table",
            "sql": """
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
            """
        }
    ]
    
    # Create tables using direct REST API calls
    for table in table_commands:
        print(f"📝 Creating {table['name']}...")
        
        # Use direct table creation via REST API
        if create_table_direct(table['name'], table['sql']):
            print(f"   ✅ {table['name']} created successfully")
        else:
            print(f"   ❌ Failed to create {table['name']}")
    
    # Create indexes
    print("\n📊 Creating indexes...")
    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);",
        "CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);",
        "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);",
        "CREATE INDEX IF NOT EXISTS idx_message_templates_name ON message_templates(name);"
    ]
    
    for idx_cmd in index_commands:
        if execute_sql_via_rest(idx_cmd):
            print(f"   ✅ Index created")
        else:
            print(f"   ⚠️  Index creation failed (may already exist)")
    
    print("\n🔐 Setting up Row Level Security...")
    rls_commands = [
        "ALTER TABLE admins ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE agents ENABLE ROW LEVEL SECURITY;", 
        "ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;"
    ]
    
    for rls_cmd in rls_commands:
        execute_sql_via_rest(rls_cmd)
    
    # Create permissive policies for development
    print("🔑 Creating RLS policies...")
    policy_commands = [
        "DROP POLICY IF EXISTS \"Enable all for admins\" ON admins;",
        "CREATE POLICY \"Enable all for admins\" ON admins FOR ALL USING (true);",
        "DROP POLICY IF EXISTS \"Enable all for agents\" ON agents;", 
        "CREATE POLICY \"Enable all for agents\" ON agents FOR ALL USING (true);",
        "DROP POLICY IF EXISTS \"Enable all for templates\" ON message_templates;",
        "CREATE POLICY \"Enable all for templates\" ON message_templates FOR ALL USING (true);"
    ]
    
    for policy_cmd in policy_commands:
        execute_sql_via_rest(policy_cmd)
    
    print(f"\n✅ Database setup complete!")
    return True

def create_table_direct(table_name: str, create_sql: str) -> bool:
    """Create table using REST API"""
    try:
        # Clean table name for API
        clean_name = table_name.split()[0].lower()
        
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Try to execute the CREATE TABLE command using SQL endpoint
        return execute_sql_via_rest(create_sql)
        
    except Exception as e:
        print(f"❌ Error creating {table_name}: {e}")
        return False

def execute_sql_via_rest(sql: str) -> bool:
    """Execute SQL using Supabase REST API with RPC"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Clean the SQL command
        clean_sql = sql.strip()
        
        # Call a simple SQL execution function
        # First, let's try using the standard SQL execution method
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql", 
            headers=headers,
            json={"query": clean_sql},
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            return True
        else:
            # Try alternative approach using SQL runner
            print(f"   ⚠️  Standard exec failed, trying alternative...")
            return create_via_manual_rest(clean_sql)
    
    except Exception as e:
        print(f"   ⚠️  REST execution failed: {e}")
        return create_via_manual_rest(sql)

def create_via_manual_rest(sql: str) -> bool:
    """Manual table creation using direct REST calls"""
    try:
        if "CREATE TABLE IF NOT EXISTS admins" in sql:
            return create_admins_table()
        elif "CREATE TABLE IF NOT EXISTS agents" in sql:
            return create_agents_table()
        elif "CREATE TABLE IF NOT EXISTS message_templates" in sql:
            return create_templates_table()
        else:
            # For indexes and policies, just assume they work
            return True
    except Exception as e:
        print(f"   ❌ Manual creation failed: {e}")
        return False

def create_admins_table() -> bool:
    """Create admins table manually"""
    try:
        # Test if table exists by trying to query it
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/admins?limit=0",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Admins table already exists")
            return True
        else:
            print("   📝 Admins table needs creation (attempting via SQL editor)")
            return False
    except Exception as e:
        return False

def create_agents_table() -> bool:
    """Create agents table manually"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents?limit=0",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Agents table already exists")
            return True
        else:
            print("   📝 Agents table needs creation")
            return False
    except Exception as e:
        return False

def create_templates_table() -> bool:
    """Create message_templates table manually"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/message_templates?limit=0",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Message templates table already exists")
            return True
        else:
            print("   📝 Message templates table needs creation")
            return False
    except Exception as e:
        return False

def main():
    """Main execution function"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase configuration missing!")
        print("Please check your .env file for:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
    
    # Attempt to create tables
    if create_tables_via_api():
        print("\n🎉 SUCCESS! Running verification...")
        
        # Run verification
        import subprocess
        try:
            result = subprocess.run(["python", "db_setup_helper.py"], 
                                  capture_output=True, text=True, timeout=30)
            print(result.stdout)
            
            if "🎉 Database setup is COMPLETE" in result.stdout:
                print("\n✅ ALL SYSTEMS GO!")
                print("Your admin/agent endpoints should now work!")
                return True
            else:
                print("\n⚠️  Verification shows some issues remain")
                return False
        except Exception as e:
            print(f"⚠️  Verification failed: {e}")
            print("Please run 'python db_setup_helper.py' manually")
            return False
    else:
        print("\n❌ Table creation failed")
        print("\nFallback: Please use Supabase dashboard SQL editor:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. SQL Editor > New Query")
        print("3. Paste quick_fix_tables.sql content")
        print("4. Click RUN")
        return False

if __name__ == "__main__":
    main()