from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements = Path("requirements.txt").read_text().splitlines()
requirements = [r.strip() for r in requirements if r.strip() and not r.startswith("#")]

# Read README
readme = Path("README.md").read_text(encoding="utf-8")

setup(
    name="cfi-midot",
    version="1.0.0",
    author="CFI MIDOT",
    author_email="itchenak@gmail.com",
    description="Financial ranking tool for Israeli NGOs",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/itchenak/CFI_MIDOT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cfi-scrape=scrape:run_scrape",
            "cfi-rank=rank:run_rank",
            "cfi-upload=upload:run_upload",
            "cfi-upload-appsheet=upload_appsheet:run_upload_appsheet",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
