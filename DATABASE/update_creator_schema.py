import psycopg2
from BACKEND.config.db_config import DB_CONFIG

def update_database():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Add role column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='students' AND column_name='role') THEN
                    ALTER TABLE students ADD COLUMN role VARCHAR(20) DEFAULT 'user';
                END IF;
            END $$;
        """)
        
        # Add is_active column if it doesn't exist (already exists in some form, but ensure boolean/int)
        # The students_table.sql has is_active SMALLINT DEFAULT 1. Let's keep it as is if it exists.
        
        # Add last_login column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='students' AND column_name='last_login') THEN
                    ALTER TABLE students ADD COLUMN last_login TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Ensure creator exists
        cur.execute("UPDATE students SET role = 'creator' WHERE email = 'gowsicklitheswaran@gmail.com'")
        
        print("Database updated successfully.")
        conn.close()
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_database()
