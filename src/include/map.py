#!/usr/bin/env python3

# Occupancy Grid Map Parsing Program
# By Ardhika Maulidani

from geometry_msgs.msg import Point
import math

class Map:
    def __init__(self, grid_map):
        # Parse map info
        self.map = grid_map                                 # Map data in row-major order [100: Occupied , -1: Unknown]
        self.width = grid_map.info.width                    # Map width [cells]
        self.height = grid_map.info.height                  # Map height [cells]
        self.resolution = grid_map.info.resolution          # Map resolution [meter/cell]
        self.frame_id = grid_map.header.frame_id            # Frame ID [default : map]

        # Parse origin coordinate from map
        self.origin = Point()                               # The origin of the map [m, m, rad]. This is the real-world pose of the cell (0,0) in the map.
        self.origin.x = grid_map.info.origin.position.x
        self.origin.y = grid_map.info.origin.position.y

    # Check is cells coordinate inside map boundaries
    def is_cell_in_range(self, i, j):
        return 0 <= i < self.height and 0 <= j < self.width
    
    # Get map data from cells coordinate
    def get_by_index(self, i, j):
        if not self.is_cell_in_range(i, j):
            raise IndexError()
        return self.map.data[i*self.width + j]

    # Get map data from meter coordinate
    def get_by_coord(self, x, y):
        return self.get_by_index(*self.m_to_cell_coordinate(x, y))

    # Convert meter to cells coordinate relative to origin
    def m_to_cell_coordinate(self, x, y):
        i = int((y - self.origin.y) / self.resolution)
        j = int((x - self.origin.x) / self.resolution)
        return (i, j)

    # Convert meter to cells coordinate relative to origin
    def cell_to_m_coordinate(self, i, j):
        y = float(i * self.resolution + self.origin.y)
        x = float(j * self.resolution + self.origin.x)
        return (x, y)
    
    def check_data(self, i, j):
        was_error = False
        try:
            cell = self.get_by_index(i, j)
        except IndexError:
            # rospy.loginfo("Coordinate are out of range")
            was_error = True
        return cell         

    # Check meter coordinate including robot size is inside map boundaries
    def is_allowed(self, i, j, robot):
        was_error = False
        side = int(math.floor((robot/self.resolution)/2))
        try:
            for s_i in range(i-side, i+side):
                for s_j in range(j-side, j+side):
                    cell = self.get_by_index(s_i, s_j)
                    if cell == 100 or cell == -1:
                        return False
        except IndexError:
            # rospy.loginfo("Coordinate are out of range")
            was_error = True
        return True and not was_error



