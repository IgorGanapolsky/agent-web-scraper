"""Package configuration for the web scraper."""
from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-web-scraper",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful web scraping solution for job listings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agent-web-scraper",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    python_requires=">=3.9",
    install_requires=[
        "playwright>=1.30.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "gspread>=5.7.0",
        "google-auth>=2.15.0",
        "python-dotenv>=0.21.0",
        "aiohttp>=3.8.0",
        "security==1.3.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "scrape-jobs=app.cli:main",
        ],
    },
)
