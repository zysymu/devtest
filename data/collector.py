import time
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
import pandas as pd


class SQLiteDataCollector:
    """
    collects all the elevator events and saves them to sqlite
    """
    
    def __init__(self, db_file: str = "elevator_simulation.db"):
        self.db_file = db_file
        self.start_time = time.time()
        self.last_request_time = self.start_time
        
        self._initialize_database()
        
    def _get_connection(self):
        """
        connect to the sqlite db
        """
        return sqlite3.connect(self.db_file)
    
    def _initialize_database(self):
        """
        set up the db table
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS elevator_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            simulation_time REAL NOT NULL,
            elevator_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            current_floor INTEGER NOT NULL,
            direction INTEGER NOT NULL,
            is_moving BOOLEAN NOT NULL,
            occupancy INTEGER NOT NULL,
            pending_requests INTEGER NOT NULL,
            time_since_last_request REAL NOT NULL,
            hour_of_day INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
         
    def record_events(self, events: List[Dict[str, Any]], building_status: Dict):
        """
        save elevator events with extra info for ML training
        """
        if not events:
            return
            
        current_time = time.time()
        simulation_time = current_time - self.start_time
        
        # get time features
        sim_datetime = datetime.fromtimestamp(current_time)
        hour_of_day = sim_datetime.hour
        day_of_week = sim_datetime.weekday()
        
        rows = []
        
        for event in events:
            # get elevator info
            elevator_id = event.get('elevator_id', 'unknown')
            elevator_info = building_status.get('elevators', {}).get(elevator_id, {})
            
            # count how many requests are still pending
            pending_requests = (
                len(elevator_info.get('up_requests', [])) + 
                len(elevator_info.get('down_requests', []))
            )
            
            time_since_last_request = current_time - self.last_request_time
            
            # write everything into a row for the db
            row_data = (
                current_time,
                simulation_time,
                elevator_id,
                event.get('type', 'unknown'),
                event.get('floor', elevator_info.get('current_floor', 0)),
                event.get('direction', 0),
                elevator_info.get('is_moving', False),
                elevator_info.get('occupancy', 0),
                pending_requests,
                time_since_last_request,
                hour_of_day,
                day_of_week,
            )
            
            rows.append(row_data)
        
        self._insert_rows(rows)
    
    def _insert_rows(self, rows: List[tuple]):
        """
        insert rows into db
        """
        insert_sql = """
        INSERT INTO elevator_events (
            timestamp, simulation_time, elevator_id, event_type, current_floor,
            direction, is_moving, occupancy, pending_requests, time_since_last_request,
            hour_of_day, day_of_week
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(insert_sql, rows)
            conn.commit()
    
    def record_request(self, floor: int, elevator_id: str):
        """
        get last request time
        """
        self.last_request_time = time.time()
    
    def get_data_summary(self) -> Dict:
        """
        get a quick summary of how much data was collected
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM elevator_events")
            event_count = cursor.fetchone()[0]
        
        return {
            'total_events': event_count,
            'storage_type': 'sqlite',
            'simulation_duration': time.time() - self.start_time
        }
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        get all the data as a pandas dataframe
        """
        query = """
        SELECT timestamp, simulation_time, elevator_id, event_type, current_floor,
               direction, is_moving, occupancy, pending_requests, time_since_last_request,
               hour_of_day, day_of_week
        FROM elevator_events 
        ORDER BY timestamp
        """
        
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn)
    
    def export_to_csv(self, filename: str = "elevator_data.csv") -> str:
        """
        export all data to a csv file
        """
        df = self.get_dataframe()
        df.to_csv(filename, index=False)
        return filename
    
    def clear_data(self):
        """
        clear all data from the database (useful for testing)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM elevator_events")
            conn.commit() 