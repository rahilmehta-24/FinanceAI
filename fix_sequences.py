"""
Fix PostgreSQL Sequences After Migration
This script resets the auto-increment sequences for all tables to prevent duplicate key errors
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

NEON_URL = os.environ.get('DATABASE_URL')

if not NEON_URL:
    print("ERROR: DATABASE_URL environment variable not set!")
    sys.exit(1)

print("=" * 70)
print("Fixing PostgreSQL Sequences")
print("=" * 70)

# Create engine
engine = create_engine(NEON_URL)

with engine.connect() as conn:
    print("\n[1/3] Fixing user table sequence...")
    result = conn.execute(text("SELECT setval('user_id_seq', (SELECT MAX(id) FROM \"user\"), true)"))
    print(f"✓ User sequence set to: {result.scalar()}")
    
    print("\n[2/3] Fixing holding table sequence...")
    result = conn.execute(text("SELECT setval('holding_id_seq', (SELECT MAX(id) FROM holding), true)"))
    print(f"✓ Holding sequence set to: {result.scalar()}")
    
    print("\n[3/3] Fixing goal table sequence...")
    # Check if there are any goals first
    count_result = conn.execute(text("SELECT COUNT(*) FROM goal"))
    goal_count = count_result.scalar()
    
    if goal_count > 0:
        result = conn.execute(text("SELECT setval('goal_id_seq', (SELECT MAX(id) FROM goal), true)"))
        print(f"✓ Goal sequence set to: {result.scalar()}")
    else:
        result = conn.execute(text("SELECT setval('goal_id_seq', 1, false)"))
        print(f"✓ Goal sequence set to: 1 (no records exist)")
    
    conn.commit()

print("\n" + "=" * 70)
print("✅ Sequences Fixed Successfully")
print("=" * 70)
print("\nYou can now:")
print("  - Register new users")
print("  - Add new holdings")
print("  - Create new goals")
print("\nwithout encountering duplicate key errors.")
