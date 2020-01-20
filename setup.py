from setuptools import setup

setup(
    name='gcloud-storage-emulator',
    version='0.1',
    description='A stub emulator for the Google Cloud Storage API',
    url='https://gitlab.com/potato-oss/gcloud-tasks-emulator',
    author='Alessandro Artoni',
    author_email='artoale@potatolondon.com',
    license='MIT',
    packages=['gcloud_storage_emulator'],
    zip_safe=False,
    scripts=[
        "bin/gcloud-storage-emulator"
    ],
    install_requires=[
        'grpcio',
        'google-cloud-storage',
        'requests',
    ]
)

