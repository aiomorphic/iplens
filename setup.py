from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="iplens",
    version="0.1.6",
    author="aiomorphic",
    author_email="iplens@proton.me",
    description="A lightweight, modern, robust IP info CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aiomorphic/iplens",
    packages=find_packages(where='src', exclude=["tests*"]),
    package_dir={'': 'src'},
    install_requires=[
        "requests>=2.25.1,<3.0.0",
        "rich>=10.0.0,<11.0.0",
    ],
    entry_points={
        "console_scripts": [
            "iplens=iplens.iplens_cli:main",
        ],
    },
    package_data={
        'iplens': ['config.cfg'],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)
