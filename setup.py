from distutils.core import setup

setup(
    name = 'emailworker',
    version = '0.1',
    packages = ['emailworker'],
    install_requires = [
        'pika'
    ]
)
