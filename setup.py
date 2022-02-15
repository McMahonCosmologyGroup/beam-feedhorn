import os
from distutils.core import setup

VERSION = '0.1'

def build_packages(base_dir, name_base):
    '''
    recusively find all the folders and treat them as packages
    '''
    arr = [name_base]
    for fname in os.listdir(base_dir):
        if os.path.isdir(base_dir+fname):
            '''
            ignore the hidden files
            '''
            if fname[0]=='.':
                continue
            name = '{}.{}'.format(name_base, fname)
            recursion = build_packages(base_dir+fname+'/', name)
            if len(recursion) != 0:
                [arr.append(rec) for rec in recursion]
    return arr

packages = build_packages('latrt-testing/', 'latrt_testing')

setup(name='holog_daq',
      version=VERSION,
      description='Software for data acquisition of the holography setup.',
      author='Grace E. Chesmore, UChicago Lab',
      author_email='chesmore@uchicago.edu',
      package_dir={'latrt_testing':'latrt-testing'},
      packages=packages,
      scripts=['scripts/make_file_psd_plot'],
     )