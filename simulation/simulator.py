import time
import random
from typing import List, Dict, Optional

from models.elevator import Elevator, RequestType
from models.building import Building
from data.collector import SQLiteDataCollector


class ElevatorSimulator:
    """
    the main simulation runner
    
    handles the loop, timing, random requests, and saving
    """
    
    def __init__(self, building: Building, data_collector: SQLiteDataCollector, tick_duration: float = 1.0):
        self.building = building
        self.data_collector = data_collector
        self.tick_duration = tick_duration
        
        self.simulation_time = 0.0
        self.tick_count = 0
        self.is_running = False
        
    def add_request(self, floor: int, request_type: RequestType = RequestType.HALL_CALL) -> bool:
        """
        add a request to the building
        """
        success = self.building.add_request(floor, request_type)
        
        # find which elevator got the request
        if success:
            elevator_id = list(self.building.elevators.keys())[0]
            self.data_collector.record_request(floor, elevator_id)
            
        return success
    
    def tick(self) -> List[dict]:
        """
        run one step of the simulation
        """
        # update building (which updates all elevators)
        events = self.building.tick(self.tick_duration)

        # record events to db
        if events:
            building_status = self.building.get_building_status()
            self.data_collector.record_events(events, building_status)
        
        # update simulation state
        self.simulation_time += self.tick_duration
        self.tick_count += 1
        
        return events
    
    def run_simulation(self, duration_seconds: float, request_frequency: float = 5.0):
        """
        run simulation for a certain duration
        generates random requests at a certain frequency
        """
        print(f"starting simulation for {duration_seconds} seconds...")
        
        self.is_running = True
        start_time = time.time()
        last_request_time = start_time
        
        # run simulation until duration is reached
        while self.is_running and (time.time() - start_time) < duration_seconds:
            # generate random requests
            current_time = time.time()
            
            # generate random requests at a certain frequency
            if current_time - last_request_time >= request_frequency:
                floor = random.choice(self.building.floors)
                if self.add_request(floor):
                    print(f"added request for floor {floor}")
                
                last_request_time = current_time
            
            # execute simulation tick
            events = self.tick()
            
            # print events
            for event in events:
                if event['type'] in ['arrived', 'became_idle']:
                    print(f"elevator {event['elevator_id']}: {event['type']} at floor {event.get('floor', 'N/A')}")
            
            # make the timer stop
            time.sleep(self.tick_duration)
        
        # stop the simulation
        self.is_running = False
        print(f"simulation completed after {self.tick_count} ticks")
        
        # print summary
        summary = self.data_collector.get_data_summary()
        print(f"collected {summary['total_events']} events")
    
    def run_scenario(self, requests: List[tuple]) -> List[dict]:
        """
        run a scenario with predefined requests
        each request is (floor, delay_seconds)
        """
        print(f"running scenario with {len(requests)} requests...")
        
        all_events = []
        scenario_start = time.time()
        
        for floor, delay in requests:
            # wait for delay
            if delay > 0:
                time.sleep(delay)
            
            # add request
            success = self.add_request(floor)
            print(f"request for floor {floor}: {'success' if success else 'failed'}")
            
            timeout = time.time() + 30 # 30 second timeout
            
            # run simulation until elevator becomes idle or timeout
            while time.time() < timeout:
                events = self.tick()
                all_events.extend(events)
                
                # check if elevator is idle (no more requests)
                building_status = self.building.get_building_status()
                all_idle = all(
                    not elevator['up_requests'] and not elevator['down_requests']
                    for elevator in building_status['elevators'].values()
                )
                
                if all_idle:
                    print(f"all elevators idle, continuing to next request...")
                    break
                
                time.sleep(self.tick_duration)
        
        scenario_duration = time.time() - scenario_start
        print(f"scenario completed in {scenario_duration:.1f} seconds")
        
        return all_events
    
    def get_simulation_status(self) -> dict:
        """
        get current simulation status
        """
        return {
            'simulation_time': self.simulation_time,
            'tick_count': self.tick_count,
            'is_running': self.is_running,
            'building_status': self.building.get_building_status(),
            'data_summary': self.data_collector.get_data_summary()
        }
    
    def stop_simulation(self):
        """
        stop the running simulation
        """
        self.is_running = False 