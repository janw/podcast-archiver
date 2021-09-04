from setuptools import setup

setup(
    name='podcast-archiver',
    version='1.0.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    scripts=['podcast_archiver.py'],
    install_requires=[
        'feedparser>=6.0.8',
        'tqdm>=4.14,<5.0',
    ],
)
