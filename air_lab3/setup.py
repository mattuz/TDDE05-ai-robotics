from setuptools import setup

package_name = 'air_lab3'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='matge373',
    maintainer_email='matge373@student.liu.se',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tst_executor = air_lab3.tst_executor:main',
            'lab3_node = air_lab3.lab3_node:main',
            'lab3_vis_node = air_lab3.lab3_vis_node:main'
        ],
    },
)
