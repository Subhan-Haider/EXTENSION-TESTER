"""Setup configuration for Extension Tester"""
from setuptools import setup, find_packages
from pathlib import Path
import sys

# Ensure Python version
if sys.version_info < (3, 9):
    sys.exit("Extension Tester requires Python 3.9 or higher")

# Read version
version_file = Path(__file__).parent / "exttester" / "__version__.py"
version_info = {}
if version_file.exists():
    exec(version_file.read_text(), version_info)
    __version__ = version_info.get('__version__', '1.0.0')
else:
    __version__ = '1.0.0'

# Read README
readme = Path(__file__).parent / "README.md"
long_description = ""
if readme.exists():
    long_description = readme.read_text(encoding='utf-8')

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements_file.exists():
    with open(requirements_file) as f:
        install_requires = [
            line.strip() for line in f 
            if line.strip() and not line.startswith('#') 
            and not line.startswith('pytest') 
            and not line.startswith('black')
            and not line.startswith('flake8')
            and not line.startswith('mypy')
        ]

setup(
    name="exttester",
    version=__version__,
    author="Subhan Haider",
    author_email="subhan.haider@example.com",
    description="Professional browser extension testing platform with real browser automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Subhan-Haider/EXTENSION-TESTER",
    project_urls={
        "Bug Tracker": "https://github.com/Subhan-Haider/EXTENSION-TESTER/issues",
        "Documentation": "https://github.com/Subhan-Haider/EXTENSION-TESTER/blob/main/README.md",
        "Source Code": "https://github.com/Subhan-Haider/EXTENSION-TESTER",
        "Changelog": "https://github.com/Subhan-Haider/EXTENSION-TESTER/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'build', 'dist']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
    ],
    keywords=[
        "browser", "extension", "testing", "chrome", "firefox", "edge",
        "automation", "playwright", "selenium", "quality-assurance",
        "security", "vulnerability", "compliance", "webextension"
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'pytest-asyncio>=0.21.1',
            'pytest-timeout>=2.2.0',
            'black>=23.12.1',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
            'bandit>=1.7.5',
        ],
        'gui': [
            'PyQt5>=5.15.9',
        ],
        'all': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'PyQt5>=5.15.9',
            'black>=23.12.1',
            'flake8>=7.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'exttester=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'exttester': [
            '*.json',
            '*.txt',
            'data/*',
        ],
    },
    zip_safe=False,
)
