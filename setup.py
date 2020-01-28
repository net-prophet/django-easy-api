from setuptools import setup, find_packages
import version

VERSION = version.get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()


setup(
    name='django-easy-api',
    version=VERSION,
    description='Configurable, flexible, instant APIs and admin pages for Django apps',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Leeward Bound',
    author_email='lee@net-prophet.tech',
    url='https://code.netprophet.tech/netp/django-easy-api',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    include_package_data=True,
    install_requires = [
        'django>=2.0',
        'djangorestframework',
        'graphene-django==2.8.0',
        'django-filter',
        'django-cors-headers',
        'django-rest-framework-simplejwt',
    ],
    dependency_links=[
        'git+https://github.com/leewardbound/graphene-django@feature/disable-serializermutation-enums#egg=graphene-django-2.8.0'
    ]
)
