#!/usr/bin/env python3
"""
Database setup script for DashCapital
Run this script to create the database and tables
"""

import pymysql
from app import app, db, User
from werkzeug.security import generate_password_hash
from decimal import Decimal

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        # Update these credentials to match your MySQL installation
        connection = pymysql.connect(
            host='localhost',
            user='root',  # Your MySQL username (usually 'root')
            password='1234'  # Your MySQL root password
        )
        
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS dashcapital")
            print("✅ Database 'dashcapital' created successfully!")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create all tables"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ All tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

# def create_sample_users():
#     """No sample users - users will register themselves"""
#     print("ℹ️  No sample users created - users can register through the application")
#     return True

def main():
    print("🚀 Setting up DashCapital Database...")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        return
    
    # Step 2: Create tables
    if not create_tables():
        return
    
    # Step 3: Ready for user registration
    print("ℹ️  No sample users created - users can register through the application")

    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Run the application: python app.py")
    print("2. Open http://localhost:5000 in your browser")
    print("3. Register your first user account")
    print("4. Start using the money request features!")

if __name__ == '__main__':
    main()
