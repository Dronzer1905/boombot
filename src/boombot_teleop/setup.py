from setuptools import find_packages, setup

package_name = 'boombot_teleop'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your_email@domain.com',
    description='Joystick teleoperation and serial communication for Boombot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'joystick_publisher = boombot_teleop.joy_pub:main',
            'serial_transmitter = boombot_teleop.serial_send:main',
        ],
    },
)
