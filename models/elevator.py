from enum import Enum
from typing import Set, List, Optional


class Direction(Enum):
    """
    which way the elevator is moving
    """
    DOWN = -1
    IDLE = 0
    UP = 1

class RequestType(Enum):
    """
    different kinds of elevator requests
    """
    HALL_CALL = "hall_call" # someone outside requested the elevator on a floor
    CAR_CALL = "car_call" # someone inside pressed a destination

class Elevator:
    """
    elevator entity

    uses SCAN algorithm: keep going in one direction until no more requests, then turn around
    example: at floor 1, requests for 3,2,5 -> goes 2,3,5 (not 2,3,back to 2,then 5)
    """

    def __init__(self, elevator_id: str, floors: List[int], capacity: int):
        self.id = elevator_id
        self.floors = floors
        self.capacity = capacity

        # initial state
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.occupancy = 0 # number of people inside
        self.is_moving = False

        # separate queues for up/down requests
        self.up_requests: Set[int] = set()
        self.down_requests: Set[int] = set()

        # timing for stats
        self.time_moving = 0.0
        self.time_idle = 0.0

        # business rules vars
        self.capacity_threshold = 0.8 # 80% full = stop accepting hall calls
        self.maintenance_threshold = 300.0 # 5 minutes of movement = forced break
        self.maintenance_rest_time = 30.0 # 30 seconds of forced rest
        self.maintenance_timer = 0.0
        self.is_maintenance_mode = False

    def add_request(self, floor: int, request_type: RequestType) -> bool:
        """
        adds a request to the relevant queue

        business rule: if elevator is full (80%+), ignore hall calls
        (people already inside can still pick destinations though)
        """
        # check if the floor is valid
        if floor not in self.floors:
            return False

        # check if the elevator is already at the floor
        if floor == self.current_floor:
            return False

        # business rule 1: capacity check
        # if too full, don't let new people call the elevator
        if request_type == RequestType.HALL_CALL:
            capacity_ratio = self.occupancy / self.capacity
            if capacity_ratio >= self.capacity_threshold:
                return False

        # business rule 2: maintenance mode
        # elevator is taking a break, no new requests allowed
        if self.is_maintenance_mode:
            return False

        # add to relevant direction queue
        if floor > self.current_floor:
            self.up_requests.add(floor)
        else:
            self.down_requests.add(floor)

        return True

    def has_requests(self) -> bool:
        """
        check if there are any requests
        """
        return len(self.up_requests) > 0 or len(self.down_requests) > 0

    def get_next_floor(self) -> Optional[int]:
        """
        uses SCAN algorithm to get next floor

        keep going in same direction until no more requests that way, then switch directions
        """
        # if there are no requests, return None
        if not self.has_requests():
            return None

        # if idle, pick closest request
        if self.direction == Direction.IDLE:
            up_closest = min(self.up_requests) if self.up_requests else float('inf')
            down_closest = max(self.down_requests) if self.down_requests else float('-inf')

            up_distance = up_closest - self.current_floor
            down_distance = self.current_floor - down_closest

            if up_distance <= down_distance and self.up_requests:
                self.direction = Direction.UP
                return min(self.up_requests)
            elif self.down_requests:
                self.direction = Direction.DOWN
                return max(self.down_requests)

        # keep going in current direction if we have requests that way
        if self.direction == Direction.UP and self.up_requests:
            return min(self.up_requests)
        elif self.direction == Direction.DOWN and self.down_requests:
            return max(self.down_requests)

        # switch directions if no more requests in current direction
        if self.direction == Direction.UP and self.down_requests:
            self.direction = Direction.DOWN
            return max(self.down_requests)
        elif self.direction == Direction.DOWN and self.up_requests:
            self.direction = Direction.UP
            return min(self.up_requests)

        return None

    def move_to_floor(self, target_floor: int) -> bool:
        """
        move one elevator one floor closer to the target (we only move one floor per tick)
        """
        # if already at the target, return True
        if target_floor == self.current_floor:
            return True

        # go up/down one floor
        if target_floor > self.current_floor:
            self.current_floor += 1
            self.direction = Direction.UP
        else:
            self.current_floor -= 1
            self.direction = Direction.DOWN

        self.is_moving = True
        return self.current_floor == target_floor

    def arrive_at_floor(self) -> List[str]:
        """
        when we arrive at a floor, remove any requests for it
        """
        events = []

        # remove requests for current floor and add event
        if self.current_floor in self.up_requests:
            self.up_requests.remove(self.current_floor)
            events.append("arrived_up")

        if self.current_floor in self.down_requests:
            self.down_requests.remove(self.current_floor)
            events.append("arrived_down")

        # if no more requests, idle
        if not self.has_requests():
            self.is_moving = False
            self.direction = Direction.IDLE
            events.append("stopped")

        return events

    def tick(self, delta_time: float) -> List[dict]:
        """
        update everything that happens each tick

        includes maintenance mode: if elevator works too hard it takes a short break
        """
        events = []

        # track time spent moving vs idle
        if self.is_moving:
            self.time_moving += delta_time
        else:
            self.time_idle += delta_time

        # maintenance mode logic
        if self.is_maintenance_mode:
            self.maintenance_timer += delta_time

            # after break, return to normal
            if self.maintenance_timer >= self.maintenance_rest_time:
                self.is_maintenance_mode = False
                self.maintenance_timer = 0.0
                events.append({
                    'type': 'maintenance_complete',
                    'floor': self.current_floor,
                    'rest_time': self.maintenance_rest_time
                })

            # continue to rest
            else:
                events.append({
                    'type': 'maintenance_mode',
                    'floor': self.current_floor,
                    'remaining_time': self.maintenance_rest_time - self.maintenance_timer
                })
                return events

        # check if it's time to break
        if self.time_moving >= self.maintenance_threshold and not self.is_maintenance_mode:
            self.is_maintenance_mode = True
            self.maintenance_timer = 0.0
            self.time_moving = 0.0 # reset timer
            events.append({
                'type': 'maintenance_started',
                'floor': self.current_floor,
                'reason': 'excessive_movement'
            })
            return events

        # get next floor to visit
        next_floor = self.get_next_floor()

        # if no more requests, idle
        if next_floor is None:
            if self.is_moving:
                self.is_moving = False
                self.direction = Direction.IDLE
                events.append({
                    'type': 'became_idle',
                    'floor': self.current_floor,
                    'time_moving': self.time_moving,
                    'time_idle': self.time_idle
                })

        # move to next floor and add event
        else:
            reached = self.move_to_floor(next_floor)
            events.append({
                'type': 'moving',
                'from_floor': self.current_floor - self.direction.value,
                'to_floor': self.current_floor,
                'direction': self.direction.value,
                'target_floor': next_floor
            })

            if reached:
                arrival_events = self.arrive_at_floor()
                events.append({
                    'type': 'arrived',
                    'floor': self.current_floor,
                    'arrival_events': arrival_events,
                    'occupancy': self.occupancy
                })

        return events

    def set_occupancy(self, occupancy: int) -> bool:
        """
        set how many people are in the elevator (for testing)
        """
        if occupancy < 0 or occupancy > self.capacity:
            return False

        self.occupancy = occupancy
        return True

    def add_passengers(self, count: int) -> bool:
        """
        add people to the elevator
        """
        if self.occupancy + count > self.capacity:
            return False

        self.occupancy += count
        return True

    def remove_passengers(self, count: int) -> bool:
        """
        remove people from the elevator
        """
        if self.occupancy - count < 0:
            return False

        self.occupancy -= count
        return True

    def is_near_capacity(self) -> bool:
        """
        check if the elevator is getting full
         (used for the capacity business rule)
        """
        return (self.occupancy / self.capacity) >= self.capacity_threshold

    def get_status(self) -> dict:
        """
        get a snapshot of everything
        """
        return {
            'id': self.id,
            'current_floor': self.current_floor,
            'direction': self.direction.name,
            'is_moving': self.is_moving,
            'occupancy': self.occupancy,
            'capacity': self.capacity,
            'up_requests': list(self.up_requests),
            'down_requests': list(self.down_requests),
            'time_moving': self.time_moving,
            'time_idle': self.time_idle,

            # business rule stuff
            'is_maintenance_mode': self.is_maintenance_mode,
            'maintenance_timer': self.maintenance_timer,
            'is_near_capacity': self.is_near_capacity(),
            'capacity_ratio': self.occupancy / self.capacity if self.capacity > 0 else 0
        }
