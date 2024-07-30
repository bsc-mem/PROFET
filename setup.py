from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt', 'r') as req_file:
        return req_file.read().splitlines()

setup(
    name='profet',
    version='1.0',
    packages=find_packages(where='src/'),
    package_dir={'': 'src/'},
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            # Create command-line scripts, define them here
            'profet=profet.run:main',
        ],
    },
    data_files=[
        # Install the man page in /usr/share/man/man1
        ('share/man/man1', ['profet.1']),
    ],
    # Add other metadata about the package
    author='BSC Memory Technologies Team',
    author_email='mariana.carmin@bsc.es',
    description='Analytical model that quantifies the impact of the '
                'main memory on application performance',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/bsc-mem/PROFET',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)