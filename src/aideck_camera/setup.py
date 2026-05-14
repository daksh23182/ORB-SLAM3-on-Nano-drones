from setuptools import setup

package_name = 'aideck_camera'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sajid-javid',
    maintainer_email='daksh23182@iiitd.ac.in',
    description='AI Deck UDP Camera Publisher',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'udp_camera_node = aideck_camera.udp_camera_node:main',
           
        ],
    },
)

