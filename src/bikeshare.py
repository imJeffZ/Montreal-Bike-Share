"""Assignment 1 - Bike-share objects

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Station and Ride classes, which store the data for the
objects in this simulation.

There is also an abstract Drawable class that is the superclass for both
Station and Ride. It enables the simulation to visualize these objects in
a graphical window.
"""
from datetime import datetime
from typing import Tuple


# Sprite files
STATION_SPRITE = 'stationsprite.png'
RIDE_SPRITE = 'bikesprite.png'


class Drawable:
    """A base class for objects that the graphical renderer can be drawn.

    === Public Attributes ===
    sprite:
        The filename of the image to be drawn for this object.
    """
    
    sprite: str

    def __init__(self, sprite_file: str) -> None:
        """Initialize this drawable object with the given sprite file.
        """
        self.sprite = sprite_file

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this object at the given time.
        """
        raise NotImplementedError


class Station(Drawable):
    """A Bixi station.

    === Public Attributes ===
    capacity:
        the total number of bikes the station can store
    location:
        the location of the station in long/lat coordinates
        **UPDATED**: make sure the first coordinate is the longitude,
        and the second coordinate is the latitude.
    name: str
        name of the station
    num_bikes: int
        current number of bikes at the station

    === Representation Invariants ===
    - 0 <= num_bikes <= capacity
    """
    name: str
    location: Tuple[float, float]
    capacity: int
    num_bikes: int
    station_start: int
    station_end: int
    low_availability: float
    low_unoccupied: float

    def __init__(self, pos: Tuple[float, float], cap: int,
                 num_bikes: int, name: str) -> None:
        """Initialize a new station.

        Precondition: 0 <= num_bikes <= cap
        """
        Drawable.__init__(self, STATION_SPRITE)
        self.location = pos
        self.capacity = cap
        self.num_bikes = num_bikes
        self.name = name
        self.station_start = 0
        self.station_end = 0
        self.low_availability = float(0)
        self.low_unoccupied = float(0)

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this station for the given time.

        Note that the station's location does *not* change over time.
        The <time> parameter is included only because we should not change
        the header of an overridden method.
        """
        return self.location
    
    def update_bikes(self, delta_num_bikes: int) -> bool:
        """Update number of bikes at station returns
            True if change successful, otherwise returns False
        """
        while delta_num_bikes > 0:
            if self.num_bikes < self.capacity:
                self.num_bikes += 1
                self.station_end += 1
                delta_num_bikes -= 1
            else:
                return False
        while delta_num_bikes < 0:
            if self.num_bikes > 0:
                self.num_bikes -= 1
                self.station_start += 1
                delta_num_bikes += 1
            else:
                return False
        return True
            
    def update_time(self):
        """Update low availability and low unoccupied times,
            increment by 60 seconds
        """
        if self.num_bikes <= 5:
            self.low_availability += 60.0
        if self.capacity-self.num_bikes <= 5:
            self.low_unoccupied += 60.0
            
    def get_stats(self):
        """Returns statistics after simulation has completed
        """
        return self.station_start, self.station_end, \
            self.low_availability, self.low_unoccupied, self.name

class Ride(Drawable):
    """A ride using a Bixi bike.

    === Attributes ===
    start:
        the station where this ride starts
    end:
        the station where this ride ends
    start_time:
        the time this ride starts
    end_time:
        the time this ride ends
    start_position:
        position of starting station
    end_posision:
        position of ending station
    total_time:
        length of time the ride lasts

    === Representation Invariants ===
    - start_time < end_time
    """
    start: Station
    end: Station
    start_time: datetime
    end_time: datetime
    total_time: float

    def __init__(self, start: Station, end: Station,
                 times: Tuple[datetime, datetime]) -> None:
        """Initialize a ride object with the given start and end information.
        """
        Drawable.__init__(self, RIDE_SPRITE)
        self.start, self.end = start, end
        self.start_time, self.end_time = times[0], times[1]
        self.total_time = (times[1]-times[0]).total_seconds()

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this ride for the given time.

        A ride travels in a straight line between its start and end stations
        at a constant speed.
        """
        elapsed_time = (time-self.start_time).total_seconds()
        start_long, start_lat = self.start.get_position(time)
        end_long, end_lat = self.end.get_position(time)
        
        long = start_long+(end_long-start_long)*(elapsed_time/self.total_time)
        lat = start_lat+(end_lat-start_lat)*(elapsed_time/self.total_time)
        return long, lat

if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'typing',
            'datetime'
        ],
        'max-attributes': 15
    })
