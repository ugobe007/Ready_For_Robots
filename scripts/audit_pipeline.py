#!/usr/bin/env python3
"""Audit the entire data pipeline from database to frontend"""

import psycopg2
import os
import sys

def audit_database():
    """Check Supabase database directly"""
    print('🔍 STEP 1: DATABASE AUDIT')
    print('='*60)
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL not set!')
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check leads table
        cur.execute('SELECT COUNT(*) FROM leads')
        total = cur.fetchone()[0]
        print(f'\n📊 LEADS TABLE: {total} total rows')
        
        cur.execute("SELECT COUNT(*) FROM leads WHERE is_internal = false")
        real = cur.fetchone()[0]
        print(f'✨ Real leads (not internal): {real}')
        
        cur.execute("SELECT COUNT(*) FROM leads WHERE temperature = 'hot' OR priority_tier = 'HOT'")
        hot = cur.fetchone()[0]
        print(f'🔥 HOT leads: {hot}')
        
        # Check signals
        cur.execute('SELECT COUNT(*) FROM signals')
        signals = cur.fetchone()[0]
        print(f'\n⚡ SIGNALS TABLE: {signals} total signals')
        
        # Sample data
        cur.execute('SELECT company_name, temperature, score FROM leads WHERE is_internal = false LIMIT 3')
        samples = cur.fetchall()
        print(f'\n📋 SAMPLE DATA:')
        for s in samples:
            print(f'  - {s[0]}: {s[1]} (score: {s[2]})')
        
        cur.close()
        conn.close()
        
        print('\n✅ Database has data!')
        return real > 0
        
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

def test_api_endpoint():
    """Test the production API endpoint"""
    import requests
    
    print('\n\n🔍 STEP 2: API ENDPOINT TEST')
    print('='*60)
    
    try:
        resp = requests.get('https://ready-2-robot.fly.dev/api/leads', timeout=10)
        print(f'\nStatus: {resp.status_code}')
        
        if resp.status_code == 200:
            data = resp.json()
            print(f'Response type: {type(data)}')
            print(f'Lead count: {len(data) if isinstance(data, list) else "Not a list"}')
            
            if len(data) > 0:
                print(f'\nFirst lead: {data[0].get("company_name")}')
                print('✅ API returning data!')
                return True
            else:
                print('❌ API returns empty array!')
                return False
        else:
            print(f'❌ API returned {resp.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ API error: {e}')
        return False

def check_backend_code():
    """Check if backend is filtering out leads"""
    print('\n\n🔍 STEP 3: BACKEND CODE REVIEW')
    print('='*60)
    
    # Read the leads API endpoint
    with open('app/api/leads.py', 'r') as f:
        content = f.read()
        
    print('\nChecking app/api/leads.py...')
    
    # Look for filters
    if 'is_internal' in content:
        print('⚠️  Found is_internal filter')
    
    if '.filter(' in content:
        print('⚠️  Found .filter() calls - may be excluding data')
    
    if 'WHERE' in content or 'where' in content:
        print('⚠️  Found SQL WHERE clauses')
    
    # Show the get_leads function
    if '@router.get("/leads")' in content:
        lines = content.split('\n')
        in_function = False
        function_code = []
        
        for line in lines:
            if '@router.get("/leads")' in line or '@router.get(\'/leads\')' in line:
                in_function = True
            
            if in_function:
                function_code.append(line)
                
                # Stop at next @router or empty function
                if line.strip().startswith('@router') and len(function_code) > 5:
                    break
                if line.strip().startswith('def ') and len(function_code) > 5:
                    break
        
        print('\n📄 Current /api/leads endpoint code:')
        print('-' * 60)
        print('\n'.join(function_code[:30]))  # First 30 lines
        print('-' * 60)

if __name__ == '__main__':
    print('🚀 DATA PIPELINE AUDIT')
    print('='*60)
    
    # Run audits
    db_ok = audit_database()
    api_ok = test_api_endpoint()
    check_backend_code()
    
    # Summary
    print('\n\n📊 AUDIT SUMMARY')
    print('='*60)
    print(f'Database has data: {"✅" if db_ok else "❌"}')
    print(f'API returns data: {"✅" if api_ok else "❌"}')
    
    if db_ok and not api_ok:
        print('\n🔧 DIAGNOSIS: Data exists in database but API returns empty')
        print('   → Backend is filtering out all leads')
        print('   → Check app/api/leads.py for is_internal or other filters')
    elif not db_ok:
        print('\n🔧 DIAGNOSIS: Database is empty')
        print('   → Need to restore data from backup')
    else:
        print('\n✅ Pipeline is healthy!')
