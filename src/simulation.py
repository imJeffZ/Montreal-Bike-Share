"""Assignment 1 - Simulation

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Simulation class, which is the main class for your
bike-share simulation.

At the bottom of the file, there is a sample_simulation function that you
can use to try running the simulation at any time.
"""
import csv
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple

from bikeshare import Ride, Station
from container import PriorityQueue
from visualizer import Visualizer

# Datetime format to parse the ride data
DATETIME_FORMAT = '%Y-%m-%d %H:%M'


class Simulation:
    """Runs the core of the simulation through time.

    === Attributes ===
    all_rides:
        A list of all the rides in this simulation.
        Note that not all rides might be used, depending on the timeframe
        when the simulation is run.
    all_stations:
        A dictionary containing all the stations in this simulation.
    visualizer:
        A helper class for visualizing the simulation.
    active_rides:
        A list of the active rides in the simulation
    event_queue:
        A priority queue of the events to be processed in the simulation
    """
    all_stations: Dict[str, Station]
    all_rides: List[Ride]
    visualizer: Visualizer
    active_rides: List[Ride]
    event_queue: PriorityQueue

    def __init__(self, station_file: str, ride_file: str) -> None:
        """Initialize this simulation with the given configuration settings.
        """
        self.all_stations = create_stations(station_file)
        self.all_rides = create_rides(ride_file, self.all_stations)
        self.active_rides = []
        self.visualizer = Visualizer()
        self.event_queue = PriorityQueue()

    def run(self, start: datetime, end: datetime) -> None:
        """Run the simulation from <start> to <end>.
        """
        current_time = start
        step = timedelta(minutes=1)  # Each iteration spans one minute of time
        station_list = list(self.all_stations.values())
        for ride in self.all_rides:
            if (ride.end_time >= start and ride.end_time <= end) or \
            (ride.start_time <= end and ride.start_time >= start):
                self.event_queue.add(RideStartEvent(self, ride, start, end))
        while current_time != end:
            self._update_status(current_time)
            self.visualizer.render_drawables(station_list+\
                                             self.active_rides, current_time)
            current_time += step

        # Leave this code at the very bottom of this method.
        # It will keep the visualization window open until you close
        # it by pressing the 'X'.
        while True:
            if self.visualizer.handle_window_events():
                return  # Stop the simulation

    def _update_active_rides(self, time: datetime) -> None:
        """Update this simulation's list of active rides for the given time.

        REQUIRED IMPLEMENTATION NOTES:
        -   Loop through `self.all_rides` and compare each Ride's start and
            end times with <time>.

            If <time> is between the ride's start and end times (inclusive),
            then add the ride to self.active_rides if it isn't already in
            that list.

            Otherwise, remove the ride from self.active_rides if it is in
            that list.

        -   This means that if a ride started before the simulation's time
            period but ends during or after the simulation's time period,
            it should still be added to self.active_rides.
        """
        for ride in self.active_rides:
            if ride.end_time == time:
                ride.end.update_bikes(1)
                self.active_rides.remove(ride)
        for ride in self.all_rides:
            if ride.start_time == time and ride not in self.active_rides:
                if ride.start.update_bikes(-1):
                    self.active_rides.append(ride)

    def _update_status(self, time: datetime):
        """Wrapper method for updating this simulation's rides and station
        """
        self._update_active_rides_fast(time)
        for station in list(self.all_stations.values()):
            station.update_time()


    def calculate_statistics(self) -> Dict[str, Tuple[str, float]]:
        """Return a dictionary containing statistics for this simulation.

        The returned dictionary has exactly four keys, corresponding
        to the four statistics tracked for each station:
          - 'max_start'
          - 'max_end'
          - 'max_time_low_availability'
          - 'max_time_low_unoccupied'

        The corresponding value of each key is a tuple of two elements,
        where the first element is the name (NOT id) of the station that has
        the maximum value of the quantity specified by that key,
        and the second element is the value of that quantity.

        For example, the value corresponding to key 'max_start' should be the
        name of the station with the most number of rides started at that
        station, and the number of rides that started at that station.
        """
        stats = []
        for station in list(self.all_stations.values()):
            stats.append(station.get_stats())
        #sort list by station name
        stats = sorted(stats, key=lambda station: station[4])
        sorted_lists = []
        #a list of lists sorted by: max_start, max_end,
        #max_time_low_availability, max_time_low_unoccupied
        sorted_lists.append(sorted(stats, key=lambda station: station[0]))
        sorted_lists.append(sorted(stats, key=lambda station: station[1]))
        sorted_lists.append(sorted(stats, key=lambda station: station[2]))
        sorted_lists.append(sorted(stats, key=lambda station: station[3]))
        index = 0
        for sorted_list in sorted_lists:
        #for each of the four statistics, remove the ones with the largest
        #but also equal values,leaving the station with the "smallest" name
            while len(sorted_list) > 1:
                if sorted_list[-1][index] == sorted_list[-2][index]:
                    sorted_list.pop(-1)
                else:
                    break
            index += 1
        max_start = sorted_lists[0][-1]
        max_end = sorted_lists[1][-1]
        max_time_low_availability = sorted_lists[2][-1]
        max_time_low_unoccupied = sorted_lists[3][-1]

        return {
            'max_start': (max_start[4], max_start[0]),
            'max_end': (max_end[4], max_end[1]),
            'max_time_low_availability': (max_time_low_availability[4]\
                                          , max_time_low_availability[2]),
            'max_time_low_unoccupied': (max_time_low_unoccupied[4]\
                                        , max_time_low_unoccupied[3])
        }



    def _update_active_rides_fast(self, time: datetime) -> None:
        """Update this simulation's list of active rides for the given time.

        REQUIRED IMPLEMENTATION NOTES:
        -   see Task 5 of the assignment handout
        """
        done = False
        while not done and not self.event_queue.is_empty():
            event = self.event_queue.remove()
            if event.time > time:
                self.event_queue.add(event)
                done = True
            else:
                events = event.process()
                for event in events:
                    self.event_queue.add(event)


def create_stations(stations_file: str) -> Dict[str, 'Station']:
    """Return the stations described in the given JSON data file.

    Each key in the returned dictionary is a station id,
    and each value is the corresponding Station object.
    Note that you need to call Station(...) to create these objects!

    Precondition: stations_file matches the format specified in the
                  assignment handout.

    This function should be called *before* _read_rides because the
    rides CSV file refers to station ids.
    """
    # Read in raw data using the json library.
    with open(stations_file) as file:
        raw_stations = json.load(file)

    stations = {}
    for s in raw_stations['stations']:
        # Extract the relevant fields from the raw station JSON.
        # s is a dictionary with the keys 'n', 's', 'la', 'lo', 'da', and 'ba'
        # as described in the assignment handout.
        # NOTE: all of the corresponding values are strings, and so you need
        # to convert some of them to numbers explicitly using int() or float().
        stations[s['n']] = Station((s['lo'], s['la']),\
                                    s['da']+s['ba'], s['da'], s['s'])
    return stations


def create_rides(rides_file: str,
                 stations: Dict[str, 'Station']) -> List['Ride']:
    """Return the rides described in the given CSV file.

    Lookup the station ids contained in the rides file in <stations>
    to access the corresponding Station objects.

    Ignore any ride whose start or end station is not present in <stations>.

    Precondition: rides_file matches the format specified in the
                  assignment handout.
    """
    rides = []
    with open(rides_file) as file:
        for line in csv.reader(file):
            # line is a list of strings, following the format described
            # in the assignment handout.
            #
            # Convert between a string and a datetime object
            # using the function datetime.strptime and the DATETIME_FORMAT
            # constant we defined above. Example:
            # >>> datetime.strptime('2017-06-01 8:00', DATETIME_FORMAT)
            # datetime.datetime(2017, 6, 1, 8, 0)
            start_time = datetime.strptime(line[0], DATETIME_FORMAT)
            end_time = datetime.strptime(line[2], DATETIME_FORMAT)
            rides.append(Ride(stations[line[1]], stations[line[3]]\
                              , (start_time, end_time)))

    return rides


class Event:
    """An event in the bike share simulation.

    Events are ordered by their timestamp.
    """
    simulation: 'Simulation'
    time: datetime

    def __init__(self, simulation: 'Simulation', time: datetime) -> None:
        """Initialize a new event."""
        self.simulation = simulation
        self.time = time

    def __lt__(self, other: 'Event') -> bool:
        """Return whether this event is less than <other>.

        Events are ordered by their timestamp.
        """
        return self.time < other.time

    def process(self) -> List['Event']:
        """Process this event by updating the state of the simulation.

        Return a list of new events spawned by this event.
        """
        raise NotImplementedError


class RideStartEvent(Event):
    """An event corresponding to the start of a ride."""
    ride: Ride
    run_start: datetime
    run_end: datetime

    def __init__(self, simulation: 'Simulation', ride: Ride,\
                  run_start: datetime, run_end: datetime):
        """Initialize start event
        """
        Event.__init__(self, simulation, ride.start_time)
        self.ride = ride
        self.run_start = run_start
        self.run_end = run_end

    def process(self) -> List['Event']:
        """Process a start event, returns a list consisting of one RideEndEvent
        """
        if self.time >= self.run_start:
            self.ride.start.update_bikes(-1)
        self.simulation.active_rides.append(self.ride)
        return [RideEndEvent(self.simulation, self.ride, self.run_end)]

class RideEndEvent(Event):
    """An event corresponding to the start of a ride."""
    ride: Ride
    run_end: datetime

    def __init__(self, simulation, ride: Ride, run_end: datetime):
        Event.__init__(self, simulation, ride.end_time)
        self.ride = ride
        self.run_end = run_end

    def process(self) -> List['Event']:
        if self.time <= self.run_end:
            self.ride.end.update_bikes(1)
        self.simulation.active_rides.remove(self.ride)
        return []


def sample_simulation() -> Dict[str, Tuple[str, float]]:
    """Run a sample simulation. For testing purposes only."""
    sim = Simulation('stations.json', 'sample_rides.csv')
    sim.run(datetime(2017, 6, 1, 8, 0, 0),
            datetime(2017, 6, 1, 9, 0, 0))
    return sim.calculate_statistics()


if __name__ == '__main__':
    # Uncomment these lines when you want to check your work using python_ta!
    #import python_ta
    #python_ta.check_all(config={
    #    'allowed-io': ['create_stations', 'create_rides'],
    #    'allowed-import-modules': [
    #        'doctest', 'python_ta', 'typing',
    #        'csv', 'datetime', 'json',
    #        'bikeshare', 'container', 'visualizer'
    #    ]
    #})
    print(sample_simulation())
