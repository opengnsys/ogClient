from distutils.core import setup

setup(name='ogclient',
      version='1.0',
      description='Client for the OpenGnsys ecosystem',
      author='Soleta OpenGnsys Support Team',
      author_email='soporte-og@soleta.eu',
      url='https://github.com/opengnsys/ogClient',
      packages=['src', 'src.linux', 'src.virtual'],
      scripts=['ogclient'],
      data_files=[('cfg', ['cfg/ogclient.json']),
                  ('', ['COPYING'])]
)
