from distutils.core import setup


setup(
    name='intervalues',
    packages=['intervalues'],
    # version=version,
    description='Efficient combining of intervals of numbers.',
    author='Bert de Bruijn',
    author_email='lpdebruijn@gmail.com',
    url='https://gitlab.com/bert.debruijn/intervalues',
    # download_url='',
    install_requires=[],
    include_package_data=False,
    # package_data={'intervalues': ['intervalues/VERSION']},
    keywords=['intervals', 'continuous', 'set', 'counter'],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python",
    ],
    python_requires='~=3.10',  # I should test for more versions
)
