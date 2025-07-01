from config import BUILDING_CONFIG, SIMULATION_CONFIG, DATA_CONFIG
from models.elevator import Elevator, RequestType
from models.building import Building
from data.collector import SQLiteDataCollector
from simulation.simulator import ElevatorSimulator


def create_simulation() -> ElevatorSimulator:
    """
    set up the simulation with elevators and data collection
    """
    # create elevators
    elevators = []
    for i in range(BUILDING_CONFIG['num_elevators']):
        elevator = Elevator(
            elevator_id=f"elevator_{i+1}",
            floors=BUILDING_CONFIG['floors'],
            capacity=BUILDING_CONFIG['elevator_capacity']
        )
        elevators.append(elevator)
    
    # create building
    building = Building(
        floors=BUILDING_CONFIG['floors'],
        elevators=elevators
    )
    
    # create data collector
    data_collector = SQLiteDataCollector(DATA_CONFIG['db_file'])
    
    # create simulator
    simulator = ElevatorSimulator(
        building=building,
        data_collector=data_collector,
        tick_duration=SIMULATION_CONFIG['tick_duration']
    )
    
    return simulator


def demo_scenario():
    """
    demonstrates the elevator in a test scenario
    """
    print("=== ELEVATOR SIMULATION DEMO ===")
    
    simulator = create_simulation()
    
    # test scenario
    test_requests = [
        (3, 0), # request floor 3 immediately
        (2, 2), # request floor 2 after 2 seconds  
        (1, 3), # request floor 1 after 3 more seconds
        (0, 2), # request floor 0 after 2 more seconds
    ]
    
    print("running test scenario:")
    print("- request floor 3 (elevator should go UP)")
    print("- request floor 2 while moving up (should serve 2 then 3)")
    print("- request floor 1 and 0 (should serve both going DOWN)")
    
    events = simulator.run_scenario(test_requests)
    
    print(f"scenario generated {len(events)} events")
    
    # show final elevator state
    status = simulator.get_simulation_status()
    elevator_status = status['building_status']['elevators']['elevator_1']
    
    print("final elevator state:")
    print(f"- current floor: {elevator_status['current_floor']}")
    print(f"- direction: {elevator_status['direction']}")
    print(f"- pending requests: {elevator_status['up_requests'] + elevator_status['down_requests']}")
    print(f"- time moving: {elevator_status['time_moving']:.1f}s")
    print(f"- time idle: {elevator_status['time_idle']:.1f}s")
    print(f"- occupancy: {elevator_status['occupancy']}/{elevator_status['capacity']}")
    print(f"- near capacity: {elevator_status['is_near_capacity']}")
    print(f"- maintenance mode: {elevator_status['is_maintenance_mode']}")


def run_random_simulation():
    """
    run the simulation with random requests
    """
    print("\n=== RANDOM SIMULATION FOR DATA COLLECTION ===")
    
    simulator = create_simulation()
    
    # run for 60 seconds with requests every 8 seconds
    simulator.run_simulation(
        duration_seconds=60,
        request_frequency=8.0
    )
    
    # show data results
    summary = simulator.data_collector.get_data_summary()
    print("data summary:")
    print(f"- total events recorded: {summary['total_events']}")
    print(f"- simulation duration: {summary['simulation_duration']:.1f}s")
    print(f"- storage type: {summary['storage_type']}")
    
    # show DataFrame example
    df = simulator.data_collector.get_dataframe()
    if not df.empty:
        print(f"- df shape: {df.shape}")
        print(f"- event types: {df['event_type'].value_counts().to_dict()}")
        
        # export to CSV
        csv_file = simulator.data_collector.export_to_csv("elevator_simulation_data.csv")
        print(f"- data exported to: {csv_file}")


def main():
    """
    main function - run both demo and data collection
    """
    
    # run demo scenario first
    demo_scenario()
    
    # run random simulation
    run_random_simulation()
    
    print("simulation complete!")


if __name__ == "__main__":
    main() 