from setuptools import setup, find_packages
import glob, os


def walk_topdirs(dest, topdirs):
    # dest: where to store the walked files e.g. ''
    # topdirs: what to walk e.g. ['tests', ...]
    datafiles = []
    for topdir in topdirs:
        for dirname, dirnames, filenames in os.walk(topdir):
            datafiles.append(
                (
                    os.path.join(dest, dirname),
                    map(lambda x: os.path.join(dirname, x), filenames)
                )
            )
    return datafiles

data_files = walk_topdirs('/usr/share/pulp_auto/', ['tests'])

setup(name='pulp_auto',
      version=0.1,
      description='Pulp REST API automation library and test cases',
      author='dparalen',
      author_email='vetrisko@gmail.com',
      url='https://github.com/RedHatQE/pulp-automation',
      license='GPLv3+',
      install_requires=['nose>=1.3.0', 'requests>=1.2.3', 'PyYAML', 'qpid-python==0.26', 'gevent>=1.0.1', 'stitches', 'M2Crypto'],
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Development Status :: 4 - Beta'
      ],
      packages=find_packages(exclude=['tests*']),
      data_files=data_files
      )
