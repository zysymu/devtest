# building setup
BUILDING_CONFIG = {
    'floors': [0, 1, 2, 3, 4, 5], # available floors (0 is ground level)
    'num_elevators': 1, # number of elevators
    'elevator_capacity': 8, # max people that fit inside
}

# timing settings
SIMULATION_CONFIG = {
    'tick_duration': 1.0, # how long each tick lasts (seconds)
    'floor_travel_time': 3.0, # time to move between floors
    'door_time': 2.0,  # time for doors to open/close
    'max_wait_time': 60.0, # how long elevator waits around doing nothing
}

# where we save all the data for ML training
DATA_CONFIG = {
    'db_file': 'elevator_simulation.db', # sqlite database file
    'collect_events': True,
} 