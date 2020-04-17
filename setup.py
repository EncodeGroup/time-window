from setuptools import setup


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='time-window',
    version='0.1.0',
    description='A Time Window library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/EncodeGroup/time-window',
    author='Encode',
    author_email='devs@encodegroup.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python'
    ],
    keywords='time window',
    packages=[
        'time_window'
    ],
    install_requires=[
        'babel>=2.1.1, <3.0',
        'python-dateutil>=2.5.2, <3.0'
    ]
)
