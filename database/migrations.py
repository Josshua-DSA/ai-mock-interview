from database.manager import DatabaseManager

def run_migrations():
    """Run database migrations to ensure all tables are created"""
    db_manager = DatabaseManager()
    db_manager.init_database()
    db_manager.seed_job_market_data()
    print("Migrations completed successfully!")
    
if __name__ == "__main__":
    run_migrations()
