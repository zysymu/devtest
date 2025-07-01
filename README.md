# Elevator Simulation

## overview

the code models an elevator inspired by event-driven entities in game development systems.

the goal here is to simulate an elevator and to use this simulation to generate data to train an ML model.

## how it works

the code is split into the following:

```
devtest/
├── models/
│   ├── elevator.py      # core elevator logic
│   └── building.py      # manages the building and elevators
├── simulation/
│   └── simulator.py     # main simulation runner
├── data/
│   └── collector.py     # saves data to sqlite
├── tests/
│   └── test_elevator.py # simple tests that check if system is okay
├── config.py            # settings for the simulation
└── main.py              # demos
```

the simulation runs in discrete time steps (called _ticks_, inspired by game engines). in each tick, the elevator can move one floor.

after taking a quick look online, i found out that elevators generally use the SCAN algorithm: the elevator keeps going in one direction as long as there are requests in that direction. once it's done, it switches directions if needed. this approach is more efficient than jumping around for every new request.

we also have a couple of "business rules":
- if an elevator is 80% full, it won't accept new hall calls.
- if an elevator has been moving for 5 minutes straight, it takes a 30-second maintenance break.

both of these rules are parameterized, so their values can be changed.

## how to use it

### run the demo

to see it in action, just run:
```bash
python main.py
```

here's the terminal output:
```
=== ELEVATOR SIMULATION DEMO ===
running test scenario:
- request floor 3 (elevator should go UP)
- request floor 2 while moving up (should serve 2 then 3)
- request floor 1 and 0 (should serve both going DOWN)
running scenario with 4 requests...
request for floor 3: success
all elevators idle, continuing to next request...
request for floor 2: success
all elevators idle, continuing to next request...
request for floor 1: success
all elevators idle, continuing to next request...
request for floor 0: success
all elevators idle, continuing to next request...
scenario completed in 9.0 seconds
scenario generated 10 events
final elevator state:
- current floor: 0
- direction: IDLE
- pending requests: []
- time moving: 2.0s
- time idle: 4.0s
- occupancy: 0/8
- near capacity: False
- maintenance mode: False

=== RANDOM SIMULATION FOR DATA COLLECTION ===
starting simulation for 60 seconds...
added request for floor 3
elevator elevator_1: arrived at floor 3
added request for floor 5
elevator elevator_1: arrived at floor 5
added request for floor 2
elevator elevator_1: arrived at floor 2
added request for floor 5
elevator elevator_1: arrived at floor 5
added request for floor 3
elevator elevator_1: arrived at floor 3
added request for floor 5
elevator elevator_1: arrived at floor 5
added request for floor 3
elevator elevator_1: arrived at floor 3
simulation completed after 60 ticks
collected 34 events
data summary:
- total events recorded: 34
- simulation duration: 60.3s
- storage type: sqlite
- df shape: (34, 12)
- event types: {'moving': 23, 'arrived': 11}
- data exported to: elevator_simulation_data.csv
simulation complete!
```

### run tests
to run the tests:
```bash
python tests/test_elevator.py
```

### configuration

you can change things like the number of floors and elevators in `config.py`.

## the data

all the simulation events are saved in a sqlite database file called `elevator_simulation.db`. this makes it easy to use the data later.

here's what we save for each event:
- `timestamp`: time of the event
- `elevator_id`: id of the elevator
- `event_type`: what happened (e.g., `moving`, `arrived`, `became_idle`)
- `current_floor`: where the elevator is
- `direction`: which way the elevator is going
- `pending_requests`: how many requests are left
- `occupancy`: how many people are inside
- `time_since_last_request`: time since the last button was pressed
- `hour_of_day`: hour of day when the event happened
- `day_of_week`: day of week when the event happened

### exporting to csv

after running a simulation, the data is exported a CSV file, which allows it to be easily fed into an ML model via `pandas`.
