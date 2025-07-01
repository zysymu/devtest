import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.elevator import Elevator, RequestType, Direction
from models.building import Building
from data.collector import SQLiteDataCollector
import time


def test_elevator_basic_movement():
    """
    make sure the elevator can move around and handle basic requests
    """
    print("testing basic elevator movement...")
    
    elevator = Elevator("test_elevator", [0, 1, 2, 3, 4, 5], 8)
    
    # Test initial state
    assert elevator.current_floor == 0
    assert elevator.direction == Direction.IDLE
    assert not elevator.has_requests()
    
    # Test adding request
    success = elevator.add_request(3, RequestType.HALL_CALL)
    assert success, "Should successfully add valid request"
    assert elevator.has_requests(), "Should have pending requests"
    
    # Test movement logic
    next_floor = elevator.get_next_floor()
    assert next_floor == 3, f"Next floor should be 3, got {next_floor}"
    
    # Test moving towards target
    reached = elevator.move_to_floor(3)
    assert not reached, "Should not reach floor 3 in one move"
    assert elevator.current_floor == 1, "Should move to floor 1"
    assert elevator.direction == Direction.UP, "Should be moving UP"
    
    print("✓ Basic elevator movement tests passed")


def test_business_rule_capacity():
    """
    test the capacity rule: when elevator gets too full, stop accepting hall calls
    (but people already inside can still pick destinations)
    """
    print("testing capacity business rule...")
    
    elevator = Elevator("test_elevator", [0, 1, 2, 3, 4, 5], 8)
    
    # pack the elevator full (above 80% threshold)
    elevator.set_occupancy(7)  # 7/8 = 87.5% > 80% threshold
    
    # hall calls should be rejected when too full
    success = elevator.add_request(3, RequestType.HALL_CALL)
    assert not success, "should reject hall call when near capacity"
    
    # but people already inside can still pick destinations
    success = elevator.add_request(3, RequestType.CAR_CALL)
    assert success, "should accept car call even when near capacity"
    
    # when there's more room, hall calls work again
    elevator.set_occupancy(5)  # 5/8 = 62.5% < 80% threshold
    success = elevator.add_request(4, RequestType.HALL_CALL)
    assert success, "should accept hall call when under capacity"
    
    print("✓ capacity business rule tests passed")


def test_business_rule_maintenance():
    """Test Business Rule 2: Maintenance mode after excessive movement"""
    print("Testing maintenance business rule...")
    
    elevator = Elevator("test_elevator", [0, 1, 2, 3, 4, 5], 8)
    
    # Reduce maintenance threshold for testing (3 seconds instead of 5 minutes)
    elevator.maintenance_threshold = 3.0
    elevator.maintenance_rest_time = 1.0
    
    # Manually set time_moving to trigger maintenance (simpler test)
    elevator.time_moving = 4.0  # Above threshold
    
    # Add a request to trigger the tick logic
    elevator.add_request(2, RequestType.HALL_CALL)
    
    # Run one tick - should trigger maintenance
    events = elevator.tick(1.0)
    
    # Check that maintenance started
    maintenance_started = any(event.get('type') == 'maintenance_started' for event in events)
    assert maintenance_started, "Should trigger maintenance when time_moving exceeds threshold"
    assert elevator.is_maintenance_mode, "Should be in maintenance mode"
    
    # Test that requests are rejected during maintenance
    success = elevator.add_request(4, RequestType.HALL_CALL)
    assert not success, "Should reject requests during maintenance mode"
    
    # Simulate rest period (1 second + a bit more)
    events = elevator.tick(1.2)
    
    # Should complete maintenance
    maintenance_complete = any(event.get('type') == 'maintenance_complete' for event in events)
    assert maintenance_complete, "Should complete maintenance after rest period"
    assert not elevator.is_maintenance_mode, "Should exit maintenance mode"
    
    # Test that requests are accepted again
    success = elevator.add_request(4, RequestType.HALL_CALL)
    assert success, "Should accept requests after maintenance"
    
    print("✓ Maintenance business rule tests passed")


def test_scan_algorithm():
    """Test the SCAN algorithm with multiple requests"""
    print("Testing SCAN algorithm...")
    
    elevator = Elevator("test_elevator", [0, 1, 2, 3, 4, 5], 8)
    
    # Start at floor 1
    elevator.current_floor = 1
    
    # Add requests: 4, 2, 5 (should serve in order: 2, 4, 5)
    elevator.add_request(4, RequestType.HALL_CALL)
    elevator.add_request(2, RequestType.HALL_CALL)
    elevator.add_request(5, RequestType.HALL_CALL)
    
    # Should go to floor 2 first (closest in UP direction)
    next_floor = elevator.get_next_floor()
    assert next_floor == 2, f"Should go to floor 2 first, got {next_floor}"
    assert elevator.direction == Direction.UP, "Should be moving UP"
    
    # Simulate reaching floor 2
    elevator.current_floor = 2
    elevator.arrive_at_floor()
    
    # Next should be floor 4
    next_floor = elevator.get_next_floor()
    assert next_floor == 4, f"Should go to floor 4 next, got {next_floor}"
    
    print("✓ SCAN algorithm tests passed")


def test_building_request_distribution():
    """Test building's ability to distribute requests to elevators"""
    print("Testing building request distribution...")
    
    # Create building with one elevator
    elevator = Elevator("elevator_1", [0, 1, 2, 3, 4, 5], 8)
    building = Building([0, 1, 2, 3, 4, 5], [elevator])
    
    # Test adding request
    success = building.add_request(3)
    assert success, "Building should accept valid request"
    assert building.total_requests == 1, "Should track total requests"
    
    # Test elevator got the request
    assert elevator.has_requests(), "Elevator should have received request"
    
    # Test invalid request
    success = building.add_request(10)  # Floor doesn't exist
    assert not success, "Building should reject invalid floor"
    
    print("✓ Building request distribution tests passed")


def test_sqlite_data_collection():
    """Test SQLite data collection functionality"""
    print("Testing SQLite data collection...")
    
    # Create data collector with test database
    collector = SQLiteDataCollector("test_elevator.db")
    
    # Clear any existing data
    collector.clear_data()
    
    # Test basic event recording
    events = [
        {
            'elevator_id': 'test_elevator',
            'type': 'moving',
            'floor': 1,
            'direction': 1
        }
    ]
    
    building_status = {
        'elevators': {
            'test_elevator': {
                'current_floor': 1,
                'is_moving': True,
                'occupancy': 0,
                'up_requests': [2, 3],
                'down_requests': []
            }
        }
    }
    
    collector.record_events(events, building_status)
    
    # Test data summary
    time.sleep(0.1)  # Small delay to ensure data is recorded
    summary = collector.get_data_summary()
    assert summary['total_events'] >= 1, f"Should have recorded at least one event, got {summary['total_events']}"
    
    # Test DataFrame creation
    df = collector.get_dataframe()
    assert not df.empty, "DataFrame should not be empty"
    assert 'elevator_id' in df.columns, "DataFrame should have elevator_id column"
    assert 'event_type' in df.columns, "DataFrame should have event_type column"
    
    # Clean up test database
    collector.clear_data()
    
    print("✓ SQLite data collection tests passed")


def test_occupancy_management():
    """Test elevator occupancy management methods"""
    print("Testing occupancy management...")
    
    elevator = Elevator("test_elevator", [0, 1, 2, 3, 4, 5], 8)
    
    # Test adding passengers
    success = elevator.add_passengers(3)
    assert success, "Should successfully add passengers"
    assert elevator.occupancy == 3, "Occupancy should be 3"
    
    # Test adding too many passengers
    success = elevator.add_passengers(10)
    assert not success, "Should reject adding too many passengers"
    assert elevator.occupancy == 3, "Occupancy should remain 3"
    
    # Test removing passengers
    success = elevator.remove_passengers(2)
    assert success, "Should successfully remove passengers"
    assert elevator.occupancy == 1, "Occupancy should be 1"
    
    # Test removing too many passengers
    success = elevator.remove_passengers(5)
    assert not success, "Should reject removing too many passengers"
    assert elevator.occupancy == 1, "Occupancy should remain 1"
    
    # Test capacity checking
    elevator.set_occupancy(7)  # Above 80% threshold
    assert elevator.is_near_capacity(), "Should be near capacity"
    
    elevator.set_occupancy(5)  # Below 80% threshold
    assert not elevator.is_near_capacity(), "Should not be near capacity"
    
    print("✓ Occupancy management tests passed")


def test_integration_with_business_rules():
    """Integration test with business rules"""
    print("Testing integration with business rules...")
    
    # Create full simulation setup
    elevator = Elevator("elevator_1", [0, 1, 2, 3, 4, 5], 8)
    building = Building([0, 1, 2, 3, 4, 5], [elevator])
    
    # Set elevator near capacity
    elevator.set_occupancy(7)  # Above threshold
    
    # Try to add hall call - should be rejected
    success = building.add_request(2, RequestType.HALL_CALL)
    assert not success, "Hall call should be rejected when near capacity"
    
    # Reduce occupancy and try again
    elevator.set_occupancy(4)  # Below threshold
    success = building.add_request(2, RequestType.HALL_CALL)
    assert success, "Hall call should be accepted when below capacity"
    
    # Run a few ticks
    for i in range(10):
        events = building.tick(1.0)
        if not any(e.has_requests() for e in building.elevators.values()):
            break  # All requests served
    
    # Verify elevator handled requests
    assert not elevator.has_requests(), "All requests should be served"
    
    print("✓ Integration with business rules tests passed")


def run_all_tests():
    """run all the tests to make sure everything works"""
    print("running elevator simulation tests (with business rules)")
    print("=" * 55)
    
    try:
        test_elevator_basic_movement()
        test_business_rule_capacity()
        test_business_rule_maintenance()
        test_scan_algorithm()
        test_building_request_distribution()
        test_sqlite_data_collection()
        test_occupancy_management()
        test_integration_with_business_rules()
        
        print("\n🎉 all tests passed!")
        print("✓ basic elevator logic")
        print("✓ business rule 1: capacity management")
        print("✓ business rule 2: maintenance mode")
        print("✓ sqlite data collection")
        print("✓ integration testing")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 