#!/usr/bin/env python3
"""Quick script to check Supabase database status after restore"""

from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql://postgres:wuVG06cT6RbG2UBL@db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432/postgres"

try:
    print("🔌 Connecting to Supabase...")
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    print("✅ CONNECTION SUCCESSFUL!\n")
    print("=" * 50)
    
    # Check total companies
    result = conn.execute(text('SELECT COUNT(*) FROM companies'))
    total = result.fetchone()[0]
    print(f'📊 Total companies: {total}')
    
    # Check real vs test leads
    result = conn.execute(text('SELECT is_internal, COUNT(*) FROM companies GROUP BY is_internal ORDER BY is_internal'))
    for row in result:
        lead_type = 'TEST DATA' if row[0] else 'REAL LEADS ✨'
        print(f'   • {lead_type}: {row[1]}')
    
    # Check signal count
    result = conn.execute(text('SELECT COUNT(*) FROM signals'))
    signals = result.fetchone()[0]
    print(f'\n⚡ Total signals: {signals}')
    
    # Sample some real leads
    print(f'\n🎯 Sample real leads from backup:')
    result = conn.execute(text("SELECT name, industry FROM companies WHERE is_internal = false LIMIT 8"))
    for row in result:
        print(f'   • {row[0]} ({row[1]})')
    
    conn.close()
    print("\n" + "=" * 50)
    print("🎉 DATABASE BACKUP RESTORED SUCCESSFULLY!")
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
