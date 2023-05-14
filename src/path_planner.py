#!/usr/bin/env python3
import rospy
import cProfile

from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped

from include.map import Map
from include.robot_dimension import RobotDimension
from include.astar import AStar
from include.HybridAStar import HybridAStar


class PathPlanning:
    def __init__(self):
        self.map = None
        self.start_pose = None
        self.goal_pose = None
        
        self.robot = RobotDimension()

        self.is_working = False
        self.path_pub = rospy.Publisher("/path", Path, queue_size=1)

        rospy.Subscriber("/map", OccupancyGrid, self.map_callback)
        rospy.Subscriber("/goal", PoseStamped, self.goal_callback)
        rospy.Subscriber("/initialpose", PoseWithCovarianceStamped, self.start_callback)

    def ready_to_plan(self):
        return self.map is not None and self.start_pose is not None and self.goal_pose is not None

    def map_callback(self, grid_map):
        if not self.is_working:
            self.is_working = True
            self.map = Map(grid_map)
            rospy.loginfo("New map was set")

            # Uncomment for impoving code execution time only!!!!
            # self.start_pose = self.map.m_to_cell_coordinate(2.0221657752990723, 1.984541416168213)
            # self.goal_pose = self.map.m_to_cell_coordinate(-0.9461665153503418, -0.04367697238922119)
          
            if self.ready_to_plan():
                # cProfile.runctx('self.plan_process()', globals(), locals())  
                self.plan_process()
                
            self.is_working = False

    def goal_callback(self, goal_pose):
        if not self.is_working:
            self.is_working = True
            self.goal_pose = self.map.m_to_cell_coordinate(goal_pose.pose.position.x, goal_pose.pose.position.y)
            if self.map is not None and self.map.is_allowed(self.goal_pose[0], self.goal_pose[1], self.robot):
                rospy.loginfo("New goal pose was set: ({}, {})".format(goal_pose.pose.position.x, goal_pose.pose.position.y))
                if self.ready_to_plan():
                    self.plan_process()
            else:
                self.goal_pose = None
                rospy.logwarn("New goal is bad or no map is available")
            self.is_working = False

    def start_callback(self, start_pose):
        if not self.is_working:
            self.is_working = True
            self.start_pose = self.map.m_to_cell_coordinate(start_pose.pose.pose.position.x, start_pose.pose.pose.position.y)
            if self.map is not None and self.map.is_allowed(self.start_pose[0], self.start_pose[1], self.robot):
                rospy.loginfo("New start pose was set: ({}, {})".format(start_pose.pose.pose.position.x, start_pose.pose.pose.position.y))
                if self.ready_to_plan():
                    self.plan_process()
            else:
                self.start_pose = None
                rospy.logwarn("New start is bad or no map is available")
            self.is_working = False

    def plan_process(self):
        path_msg = Path()
        path_msg.header.stamp = rospy.Time.now()
        path_msg.header.frame_id = self.map.frame_id

        rospy.loginfo("Path planning was started...")
        path = HybridAStar.replan(self.map, self.start_pose, self.goal_pose, self.robot)
        # smooth_path = HybridAStar.smooth_path(path)
        # print(path)
        if path is not None:
            for p in path:
                pose_msg = PoseStamped()
                pose_msg.header.frame_id = path_msg.header.frame_id
                pose_msg.header.stamp = rospy.Time.now()
                pose_msg.pose.position.x = p[0]
                pose_msg.pose.position.y = p[1]
                path_msg.poses.append(pose_msg)

        self.path_pub.publish(path_msg)
        rospy.loginfo("Path published successfully")

if __name__ == '__main__':
    rospy.init_node('astar_node')
    node = PathPlanning()
    rospy.spin()