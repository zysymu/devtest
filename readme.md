# Dev Test 2022

## Elevators

The goal of this project is to model an elevator to build a prediction engine for which floor is the best resting floor at any time.
- When people call an elevator this is considered a demand
- When the elevator is vacant and not moving between floors, the current floor is considered its resting floor.
- When the elevator is vacant, it can stay at the current position or move to a different floor
- The prediction model will determine what is the best floor to rest on.


_The requirement isn't to complete this system but to start building a system that would feed into the training and prediction
of an ML system._

You will need to talk through your approach, how you modelled the data and why you thought that data was important, provide endpoints to collect the data and 
a means to store the data. Testing is important and will be used verify your system.


#### In short
- connect to a database
- crud some data (perhaps using flask)
- add some flair with a business rule or two
- have the data in a suitable format to feed to a prediction training algorithm

#### Marking
You will be marked on how well your tests cover the code and how useful they would be in a prod system.

You will need to provide a database of some sort. This could be as simple as a sqlite or as complicated as a docker container with a migrations file.

Fork this repo and begin from there.

For your submission, invite my user to review your github PR(s) into the main branch. I will review it, offer any feedback and if it passes PR you will proceed onto the next step.

Github user to invite is @dchecks

#### Time limit
Don't spend more than 8 hours on this. Projects that pass PR are paid at the standard hourly rate.
 