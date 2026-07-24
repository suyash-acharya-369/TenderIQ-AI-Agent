import sqlite3
import os

db_path = os.path.join(r"c:\Users\AUSHI SHARMA\Desktop\TENDER SEO AI AGENT", "tenderiq.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"Added {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {column} already exists in {table}")
        else:
            print(f"Error adding {column} to {table}: {e}")

add_column("notification_rules", "conditions", "JSON")
add_column("keyword_groups", "routed_teams", "JSON")
add_column("keyword_groups", "routed_roles", "JSON")
add_column("keyword_groups", "routed_recipients", "JSON")
add_column("notification_logs", "opened_at", "DATETIME")
add_column("notification_logs", "clicked_at", "DATETIME")
add_column("users", "notification_preferences", "JSON")

conn.commit()

# Create InAppNotification table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS in_app_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id VARCHAR(50) DEFAULT 'default_ws',
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    action_url VARCHAR(512),
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
""")
conn.commit()
print("Migration completed.")
conn.close()
