from setuptools import setup, find_packages

setup(
    name='gcloud-storage-emulator',
    version='0.1',
    description='A stub emulator for the Google Cloud Storage API',
    url='https://gitlab.com/potato-oss/gcloud-tasks-emulator',
    author='Alessandro Artoni',
    author_email='artoale@potatolondon.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    scripts=[
        "bin/gcloud-storage-emulator"
    ],
    install_requires=[
        'fs',
        'google-cloud-storage',
        'requests',
    ]
)
