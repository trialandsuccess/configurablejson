from distutils.core import setup

with open('README.md') as f:
    long_desc = f.read()

setup(name='Configurable JSON',
      version='1.0.0',
      description='Easily Extend the JSON Encoder with Custom Rules',
      author='Robin van der Noord',
      author_email='contact@trialandsuccess.nl',
      url='https://github.com/trialandsuccess/configurablejson',
      packages=['configurablejson'],
      long_description=long_desc,
      long_description_content_type="text/markdown",
      )
