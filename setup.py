from setuptools import setup

setup(
    name='elcap',
    version="0.1",
    author="Sebastian Kreft",
    author_email="skreft@gmail.com",
    maintainer="Sebastian Kreft",
    maintainer_email="skreft@gmail.com",
    description="A Nose plugin to mutate python source code.",
    long_description=open('./README').read(),
    url='',
    license='MIT License',
    entry_points={
        'nose.plugins.0.10': [
            'mutations = elcap.plugins:Mutations',
        ]
        },
    py_modules=['plugins'],
    install_requires=['nose>=0.11.1', 'coverage'],
    )
