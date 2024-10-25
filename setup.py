from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of the README file for long_description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Load requirements from a file
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='julien-python-toolkit',
    version='0.1.5',
    packages=find_packages(),
    license='Custom Non-Commercial License',  # Reference your custom license
    install_requires=required,  # Use the list from requirements.txt
    description='Important code that I reuse through multiple projects. Please see license for allowed use.',
    long_description=long_description,  # Include long description here
    long_description_content_type='text/markdown',  # Set to 'text/markdown' for Markdown files
    author='Julien Python',
    author_email='python.julien@hotmail.com',
    url='https://github.com/JulienPython/JulienPythonToolkit-V001',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)