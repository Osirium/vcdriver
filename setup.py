from setuptools import setup, find_packages


setup(
    version='5.1.1',
    name='vcdriver',
    description='A vcenter driver based on pyvmomi, fabric and pywinrm',
    url='https://github.com/Osirium/vcdriver',
    license='MIT',
    install_requires=['colorama', 'Fabric3', 'pyvmomi', 'pywinrm2', 'six'],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
    ],
)
