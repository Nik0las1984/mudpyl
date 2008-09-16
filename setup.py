from setuptools import setup, find_packages
import os

#we need to execute __init__.py because that's where our version number lives.
#fortunately, it has barely any code in it. This -should- work under normal
#conditions, because everything is unzipped anyway for installation.
edict = {}
execfile(os.path.join('mudpyl', '__init__.py'), edict)
setup(name = "mudpyl",
      version = edict['__version__'],
      author = 'Sam Pointon',
      author_email = 'sampointon@gmail.com',
      url = 'https://launchpad.net/mudpyl/',
      description = "Python MUD client",
      long_description = open("README").read(),
      classifiers = [
          "Development Status :: 3 - Alpha",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Topic :: Communications :: Chat",
          "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
          "Topic :: Terminals :: Telnet"
          ],
      license = 'GNU GPL v2 or later',
      install_requires = ['Twisted', 'argparse', 'ordereddict'],
      extras_require = {'rifttracker': ['peak.util.extremes'],
                        'gtkgui': ['pygtk']
                        },
      test_suite = 'nose.collector',
      packages = find_packages(),
      scripts = ['mudpyl/mudconnect.py'],
)
