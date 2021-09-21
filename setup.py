from setuptools import setup

setup(
    name='aiospotify',
    version='0.1.0',
    description='An asynchronous wrapper for the spotify web API.',
    packages=['aiospotify'],
    python_requires='>=3.8',
    install_requires=['aiohttp']
)