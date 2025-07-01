from typing import List, Dict, Optional
from .elevator import Elevator, RequestType


class Building:
    """
    building entity

    when someone calls for an elevator, we pick the best one to send
    (closest idle one, or least busy if they're all working)

    floors: list of available floors (0 is ground level)
    elevators: list of elevator objects
    total_requests: number of requests made to the building
    """
    
    def __init__(self, floors: List[int], elevators: List[Elevator]):
        self.floors = floors
        self.elevators = {elevator.id: elevator for elevator in elevators}
        self.total_requests = 0
        
    def add_request(self, floor: int, request_type: RequestType = RequestType.HALL_CALL) -> bool:
        """
        assign request to closest idle elevator or least busy one
        """
        # check if the floor is valid
        if floor not in self.floors:
            return False
            
        best_elevator = self._find_best_elevator(floor)
        
        if best_elevator:
            success = best_elevator.add_request(floor, request_type)
            if success:
                self.total_requests += 1
        
            return success
            
        return False
    
    def _find_best_elevator(self, requested_floor: int) -> Optional[Elevator]:
        """
        pick which elevator should handle this request
        prefer idle elevators, then pick the least busy one
        """
        # find idle and busy elevators
        idle_elevators = [e for e in self.elevators.values() if not e.has_requests()]
        busy_elevators = [e for e in self.elevators.values() if e.has_requests()]
        
        # if any elevators are idle, pick the closest one
        if idle_elevators:
            return min(idle_elevators, key=lambda e: abs(e.current_floor - requested_floor))
        
        # if all elevators are busy, pick the one with least requests
        if busy_elevators:
            return min(busy_elevators, key=lambda e: len(e.up_requests) + len(e.down_requests))
            
        return None
    
    def tick(self, delta_time: float) -> List[dict]:
        """
        run one tick for all elevators and collect everything
        """
        all_events = []
        
        # run one tick for each elevator
        for elevator in self.elevators.values():
            events = elevator.tick(delta_time)
            
            # tag each event with elevator ID
            for event in events:
                event['elevator_id'] = elevator.id
                all_events.append(event)
                
        return all_events
    
    def get_building_status(self) -> dict:
        """
        get a snapshot of the whole building
        """
        return {
            'total_elevators': len(self.elevators),
            'total_requests': self.total_requests,
            'elevators': {eid: elevator.get_status() for eid, elevator in self.elevators.items()},
            'floors': self.floors
        }

