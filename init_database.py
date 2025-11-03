"""
Database initialization script
Run this to create the database and tables
"""

from app.database import init_db
from app.config import settings

def main():
    print("🔧 Initializing Blood Report Analyzer Database...")
    print(f"📁 Database URL: {settings.DATABASE_URL}")
    
    # Create directories
    print("\n📂 Creating directories...")
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   ✓ Created: {settings.UPLOAD_DIR}")
    
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   ✓ Created: {settings.CHROMA_PERSIST_DIR}")
    
    settings.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   ✓ Created: {settings.KNOWLEDGE_BASE_DIR}")
    
    # Initialize database
    print("\n🗄️  Creating database tables...")
    init_db()
    
    print("\n✅ Database initialization complete!")
    print("\nYou can now run the server:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()