import sqlite3
import logging
import json

class GuildDataManager:
    def __init__(self, db_path='guild_data.db'):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def add_new_field(self, field_name, field_type="TEXT"):
        """Add a new field to the guild_settings table."""
        query = f"ALTER TABLE guild_settings ADD COLUMN {field_name} {field_type}"
        try:
            self.conn.execute(query)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            # This error typically occurs if the column already exists
            self.logger.error(f"Error adding new field: {e}")

    def create_table(self):
        """Create the table if it doesn't exist."""
        query = '''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def set_guild_setting(self, guild_id, setting, value):
        """Set a specific setting for a guild."""
        if isinstance(value, list):
            value = json.dumps(value)  # Serialize list to JSON string
            
        if not self.column_exists('guild_settings', setting):
            self.add_column('guild_settings', setting)

        query = f'INSERT INTO guild_settings (guild_id, {setting}) VALUES (?, ?) ' \
                f'ON CONFLICT(guild_id) DO UPDATE SET {setting} = ?'
        self.conn.execute(query, (guild_id, value, value))
        self.logger.info(f"Set {setting} = {value} for guild ID {guild_id}")
        self.conn.commit()

    def column_exists(self, table, column):
        """Check if a column exists in the specified table."""
        query = f"PRAGMA table_info({table})"
        columns = [row[1] for row in self.conn.execute(query)]
        return column in columns

    def add_column(self, table, column, data_type='TEXT'):
        """Add a new column to a table."""
        query = f"ALTER TABLE {table} ADD COLUMN {column} {data_type}"
        self.conn.execute(query)
        self.conn.commit()


    def get_guild_setting(self, guild_id, setting, default=None):
        """Get a specific setting for a guild."""
        if not self.column_exists('guild_settings', setting):
            self.add_column('guild_settings', setting)
            return default

        query = f'SELECT {setting} FROM guild_settings WHERE guild_id = ?'
        self.logger.info(f"Got {setting} for {guild_id}")
        cursor = self.conn.execute(query, (guild_id,))
        result = cursor.fetchone()
        if result and result[0] is not None:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return result[0]
        return default

    def close(self):
        """Close the database connection."""
        self.conn.close()
