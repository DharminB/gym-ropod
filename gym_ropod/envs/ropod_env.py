from abc import abstractmethod

import os
import subprocess
import time
from termcolor import colored
import std_srvs.srv as std_srvs

import gym
import rospy

class RopodEnv(gym.Env):
    '''An abstract base class for ROPOD environments. Reuses most of
    https://github.com/ascane/gym-gazebo-hsr/blob/master/gym_gazebo_hsr/envs/gazebo_env.py

    Constructor arguments:
    launch_file_path: str -- absolute path to a launch file that starts the ROPOD simulation

    The constructor raises an IOError if the specified launch file path does not exist.

    '''
    def __init__(self, launch_file_path: str,
                 roscore_port: str='11311',
                 reset_sim_srv_name: str='/gazebo/reset_world'):
        if not os.path.exists(launch_file_path):
            raise IOError('{0} is not a valid launch file path'.format(launch_file_path))

        print(colored('[RopodEnv] Launching roscore...', 'green'))
        self.roscore_process = subprocess.Popen(['roscore', '-p', roscore_port])
        time.sleep(1)
        print(colored('[RopodEnv] Roscore launched!', 'green'))

        print(colored('[RopodEnv] Launching simulator...', 'green'))
        self.sim_process = subprocess.Popen(['roslaunch', '-p', roscore_port,
                                             launch_file_path, 'gui:=false'])
        print(colored('[RopodEnv] Simulator launched!', 'green'))

        print(colored('[RopodEnv] Waiting for service {0}'.format(reset_sim_srv_name), 'green'))
        rospy.wait_for_service(reset_sim_srv_name)
        self.reset_sim_proxy = rospy.ServiceProxy(reset_sim_srv_name, std_srvs.Empty)
        print(colored('[RopodEnv] Service {0} is up'.format(reset_sim_srv_name), 'green'))

        self.sim_vis_process = None

        print(colored('[RopodEnv] Initialising ROS node', 'green'))
        rospy.init_node('gym')
        print(colored('[RopodEnv] ROS node initialised', 'green'))

    @abstractmethod
    def step(self, action: int):
        '''Runs a single step through the simulation.

        Keyword arguments:
        action: int -- an action to execute

        '''
        raise NotImplementedError()

    @abstractmethod
    def reset(self):
        '''Resets the simulation environment.
        '''
        raise NotImplementedError()

    def render(self, mode: str='human'):
        '''Displays the current environment. Opens up a simulation process
        if the environment is being rendered for the first time.

        Keyword arguments:
        mode: str -- rendering mode (default "human")

        '''
        if self.sim_vis_process is None or self.sim_vis_process.poll() is not None:
            self.sim_vis_process = subprocess.Popen('gzclient')

    def close(self):
        '''Closes the simulation client and terminates the simulation and roscore processes.
        '''
        self._close_sim_client()
        self.sim_process.terminate()
        self.roscore_process.terminate()
        self.sim_process.wait()
        self.roscore_process.wait()

    def _close_sim_client(self):
        '''Stops the process running the simulation client.
        '''
        if self.sim_vis_process is not None and self.sim_vis_process.poll() is None:
            self.sim_vis_process.terminate()
            self.sim_vis_process.wait()
