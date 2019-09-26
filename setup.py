from setuptools import setup, find_packages


with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='django_data_sync',
    version='0.5.2',
    description='Sync database between Django backends',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/unit9/django-data-sync',
    author='Abirafdi Raditya Putra',
    author_email='raditya.putra@unit9.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'google-cloud-tasks==1.1.0',
        'cryptography==2.7',
        'PyJWT==1.7.1',
        'oidc-validators==0.5.2'
    ],
    zip_safe=False,
    python_requires=">=3.7",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
