from DATABASE.connection.db_connection import execute_insert, execute_query

def migrate():
    print("Running Migration...")
    # 1. Create system_config table for Global Face Toggle
    execute_insert("""
        CREATE TABLE IF NOT EXISTS system_config (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT
        );
    """)
    # Seed face_verification_enabled = 'ON'
    execute_insert("""
        INSERT INTO system_config (setting_key, setting_value)
        VALUES ('face_verification_enabled', 'ON')
        ON CONFLICT (setting_key) DO NOTHING
    """)

    # Seed fingerprint_verification_enabled = 'OFF'
    execute_insert("""
        INSERT INTO system_config (setting_key, setting_value)
        VALUES ('fingerprint_verification_enabled', 'OFF')
        ON CONFLICT (setting_key) DO NOTHING
    """)
    
    # 2. Add Columns to attendance
    cols = execute_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'attendance'")
    existing_cols = [c['column_name'] for c in cols]
    
    if 'fingerprint_verified' not in existing_cols:
        execute_insert("ALTER TABLE attendance ADD COLUMN fingerprint_verified BOOLEAN DEFAULT FALSE")
        print("- Added fingerprint_verified")

    if 'marked_by_name' not in existing_cols:
        execute_insert("ALTER TABLE attendance ADD COLUMN marked_by_name VARCHAR(100)")
        print("- Added marked_by_name")
    
    if 'grace_timer_started_at' not in existing_cols:
        execute_insert("ALTER TABLE attendance ADD COLUMN grace_timer_started_at TIMESTAMP")
        print("- Added grace_timer_started_at")
        
    if 'grace_timer_passed' not in existing_cols:
        execute_insert("ALTER TABLE attendance ADD COLUMN grace_timer_passed BOOLEAN DEFAULT FALSE")
        print("- Added grace_timer_passed")

    if 'face_enabled' not in existing_cols:
        execute_insert("ALTER TABLE attendance ADD COLUMN face_enabled BOOLEAN DEFAULT TRUE")
        print("- Added face_enabled")

    print("Migration Complete.")

if __name__ == '__main__':
    migrate()
