"""
Database Migration Script: SQLite to NeonDB
This script migrates all data from the local SQLite database to NeonDB (PostgreSQL)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database URLs
SQLITE_URL = 'sqlite:///instance/finance.db'
NEON_URL = os.environ.get('DATABASE_URL')

if not NEON_URL:
    print("ERROR: DATABASE_URL environment variable not set!")
    sys.exit(1)

print("=" * 70)
print("Database Migration: SQLite -> NeonDB")
print("=" * 70)
print(f"\nSource: {SQLITE_URL}")
print(f"Target: NeonDB (connection string found)")
print()

# Create engines
sqlite_engine = create_engine(SQLITE_URL)
neon_engine = create_engine(NEON_URL)

# Import models to ensure tables are created
from models import User, Holding, Goal
from extensions import db
from app import create_app

# Create Flask app to initialize SQLAlchemy
app = create_app()

with app.app_context():
    print("[1/6] Dropping existing tables in NeonDB (if any)...")
    db.drop_all()
    print("✓ Tables dropped")
    
    print("\n[2/6] Creating tables in NeonDB...")
    db.create_all()
    print("✓ Tables created successfully")
    
    print("\n[3/6] Reading data from SQLite...")
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()
    
    # Read all data
    users = sqlite_session.execute(text("SELECT * FROM user")).fetchall()
    holdings = sqlite_session.execute(text("SELECT * FROM holding")).fetchall()
    goals = sqlite_session.execute(text("SELECT * FROM goal")).fetchall()
    
    print(f"  - Users: {len(users)}")
    print(f"  - Holdings: {len(holdings)}")
    print(f"  - Goals: {len(goals)}")
    
    if len(users) == 0:
        print("\n⚠ No data found in SQLite database. Migration complete (no data to migrate).")
        sqlite_session.close()
        sys.exit(0)
    
    print("\n[4/6] Migrating Users...")
    for row in users:
        user = User(
            id=row[0],
            email=row[1],
            username=row[2],
            password_hash=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.utcnow()
        )
        db.session.add(user)
    db.session.commit()
    print(f"✓ Migrated {len(users)} users")
    
    print("\n[5/6] Migrating Holdings...")
    for row in holdings:
        holding = Holding(
            id=row[0],
            user_id=row[1],
            symbol=row[2],
            company_name=row[3],
            quantity=row[4],
            buy_price=row[5],
            buy_date=datetime.fromisoformat(row[6]).date() if row[6] else None,
            sector=row[7],
            created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.utcnow()
        )
        db.session.add(holding)
    db.session.commit()
    print(f"✓ Migrated {len(holdings)} holdings")
    
    print("\n[6/6] Migrating Goals...")
    for row in goals:
        goal = Goal(
            id=row[0],
            user_id=row[1],
            name=row[2],
            goal_type=row[3],
            target_amount=row[4],
            current_savings=row[5],
            monthly_contribution=row[6],
            expected_return=row[7],
            target_date=datetime.fromisoformat(row[8]).date() if row[8] else None,
            created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.utcnow()
        )
        db.session.add(goal)
    db.session.commit()
    print(f"✓ Migrated {len(goals)} goals")
    
    # Verify migration
    print("\n" + "=" * 70)
    print("Verification:")
    print("=" * 70)
    neon_users = db.session.query(User).count()
    neon_holdings = db.session.query(Holding).count()
    neon_goals = db.session.query(Goal).count()
    
    print(f"  NeonDB Users: {neon_users} (Expected: {len(users)})")
    print(f"  NeonDB Holdings: {neon_holdings} (Expected: {len(holdings)})")
    print(f"  NeonDB Goals: {neon_goals} (Expected: {len(goals)})")
    
    if neon_users == len(users) and neon_holdings == len(holdings) and neon_goals == len(goals):
        print("\n✅ Migration completed successfully! All data verified.")
    else:
        print("\n⚠ Warning: Record counts don't match. Please verify manually.")
    
    sqlite_session.close()

print("\n" + "=" * 70)
print("Migration Complete")
print("=" * 70)
