from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'boombot_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # 1. Install the launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # 2. Install the URDF files
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dronzer',
    maintainer_email='dronzer@todo.todo',
    description='Gazebo Harmonic simulation for Boombot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 3. Register the mock OAK-D executable
            'mock_oakd = boombot_sim.mock_oakd:main',
            'sim_joystick = boombot_sim.sim_joystick_teleop:main'
        ],
    },
)