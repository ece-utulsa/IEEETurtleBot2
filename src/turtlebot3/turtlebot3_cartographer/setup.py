from setuptools import find_packages, setup
import os  
from glob import glob

package_name = 'turtlebot3_cartographer'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rats',
    maintainer_email='156852328+mauratoney@users.noreply.github.com',
    description='send commands to Pi for Turtlebot burger',
    license='Apache-2.0',
    tests_require=['pytest'],
)
