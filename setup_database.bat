@echo off
echo ========================================
echo   SUPABASE DATABASE SETUP - ONE CLICK
echo ========================================
echo.
echo 🚀 Opening Supabase dashboard...
start https://supabase.com/dashboard/project/jpdgkorskxfmgkbdbaig/sql/new

echo.
echo 📝 The SQL script is ready below. COPY THIS ENTIRE BLOCK:
echo.
echo ========== COPY FROM HERE ==========
type quick_fix_tables.sql
echo ========== COPY UNTIL HERE ==========
echo.
echo 📋 INSTRUCTIONS:
echo 1. The Supabase SQL Editor is now opening in your browser
echo 2. Copy the SQL script above (between the === lines)
echo 3. Paste it in the SQL Editor
echo 4. Click the blue "RUN" button
echo 5. You should see "✅ CRITICAL TABLES CREATED!"
echo.
echo 🔍 After running SQL, this script will auto-verify...
echo Press any key when you've run the SQL script...
pause
echo.
echo 🧪 Checking database setup...
python db_setup_helper.py
echo.
echo 🧪 Testing endpoints...  
python test_endpoints.py
echo.
echo ✅ Setup complete! Your admin/agent endpoints should work now.
echo Press any key to exit...
pause