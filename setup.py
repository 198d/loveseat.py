from setuptools import setup

setup(name='loveseat',
      version='0.2.0',
      description='Loveseat is a CouchDB client and document mapper.',
      author='John MacKenzie',
      author_email='john@nineteeneightd.com',
      url='http://nineteeneightd.com/loveseat.py/',
      install_requires=['requests>=1.1.0,<1.2'],
      packages=['loveseat'])
