from distutils.core import setup, Extension

module1 = Extension('cscan',
                    sources = ['main.c'])

setup (name = 'CBufferScan',
       version = '0.1',
       description = 'Fast scanning of large buffers',
       ext_modules = [module1])