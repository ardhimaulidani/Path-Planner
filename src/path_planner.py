#!/usr/bin/env python3
import tf
import rospy
import cProfile
import math

from std_msgs.msg import Bool
from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped

from include.map import Map
from include.robot_dimension import RobotDimension
from include.HybridAStar import HybridAStar

class PathPlanning:
    def __init__(self):
        self.map = None
        self.start_pose = None
        self.goal_pose = None
        self.prev_crash_status = False

        self.robot = RobotDimension(0.7, 0.7)

        self.is_working = False
        self.path_pub = rospy.Publisher("/path", Path, queue_size=1)

        rospy.Subscriber("/map", OccupancyGrid, self.map_callback)
        rospy.Subscriber("/goal", PoseStamped, self.goal_callback)
        rospy.Subscriber("/crashed", Bool, self.crashed_callback)
        rospy.Subscriber("/amcl_pose", PoseWithCovarianceStamped, self.start_callback)

    def ready_to_plan(self):
        return self.map is not None and self.start_pose is not None and self.goal_pose is not None

    def crashed_callback(self, crashed_status):
        if not self.is_working:
            self.is_working = True        
            self.crashed_status = crashed_status.data
            if self.prev_crash_status == 0 and self.crashed_status == 1:
                if self.ready_to_plan():
                    rospy.loginfo("Updating plan...")    
                    self.plan_process()
            self.prev_crash_status = self.crashed_status
            self.is_working = False


    def map_callback(self, grid_map):
        if not self.is_working:
            self.is_working = True
            self.map = Map(grid_map)
            rospy.loginfo("New map was updated")

            # Uncomment for impoving code execution time only!!!!
            # self.start_pose = self.map.m_to_cell_coordinate(2.0221657752990723, 1.984541416168213)
            # self.goal_pose = self.map.m_to_cell_coordinate(-0.9461665153503418, -0.04367697238922119)
        
            # if self.ready_to_plan(): 
            #     self.plan_process()
                # cProfile.runctx('self.plan_process()', globals(), locals()) 
                
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
            #     if self.ready_to_plan():
            #         self.plan_process()
            else:
                self.start_pose = None
                rospy.logwarn("New start is bad or no map is available")
            self.is_working = False

    def angle(self, current_pose, next_pose):
        dy = next_pose[1] - current_pose[1]
        dx = next_pose[0] - current_pose[0]
        return math.atan2(dx, dy)
 
    # Convert Euler Yaw to Quaternion
    def Euler_to_Quat(self, theta, pose_msg):
        quaternion = tf.transformations.quaternion_from_euler(0, 0, theta)
        pose_msg.pose.orientation.x = quaternion[0]
        pose_msg.pose.orientation.y = quaternion[1]
        pose_msg.pose.orientation.z = quaternion[2]
        pose_msg.pose.orientation.w = quaternion[3]

        return pose_msg.pose.orientation
        
    def plan_process(self):
        path_msg = Path()
        path_msg.header.stamp = rospy.Time.now()
        path_msg.header.frame_id = self.map.frame_id

        rospy.loginfo("Path planning was started...")
        path = HybridAStar.replan(self.map, self.start_pose, self.goal_pose, self.robot)
        # smooth_path = HybridAStar.smooth_path(path)

        if path is not None:
            for p in range(0, len(path) - 1):
                # Initialize Current Path and Next Path
                p1 = path[p]
                p2 = path[p+1]
                # Initialize Pose Messages
                pose_msg = PoseStamped()
                pose_msg.header.frame_id = path_msg.header.frame_id
                pose_msg.header.stamp = rospy.Time.now()
                # Push Position to Pose Messages
                pose_msg.pose.position.x = p1[0]
                pose_msg.pose.position.y = p1[1]
                pose_msg.pose.orientation = self.Euler_to_Quat(self.angle(p1, p2), pose_msg)
                path_msg.poses.append(pose_msg)

        self.path_pub.publish(path_msg)
        rospy.loginfo("Path published successfully")

if __name__ == '__main__':
    rospy.init_node('astar_node')
    node = PathPlanning()
    rospy.spin()