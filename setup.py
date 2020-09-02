"""setuptools module for solana.py."""

from setuptools import find_packages, setup

extras_require = {
    "dev": [
        "black",
        "pytest",
        "pylint",
        "pytest-tornasync",
        "mypy",
        "pydocstyle",
        "flake8",
        "isort",
        "pytest-docker",
        "sphinx",
        "twine",
        "setuptools",
        "bump2version",
    ]
}

with open("README.md", "r") as file_handle:
    README_MD = file_handle.read()

setup(
    name="solana",
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version="0.1.1",
    author="Michael Huang",
    author_mail="michaelhly@gmail.com",
    description="""Solana.py""",
    long_description=README_MD,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "base58>=2.0.1, <3.0.0",
        "PyNaCl>=1.4.0, <2.0.0",
        "requests>=2.24.0, <3.0.0",
        "typing_extensions",
    ],
    extras_require=extras_require,
    python_requires=">=3.7, <4",
    keywords="solana blockchain web3",
    license="MIT",
    package_data={"solana": ["py.typed"]},
    packages=find_packages(exclude=["tests", "tests.*"]),
    url="https://github.com/michaelhly/solanapy",
    zip_safe=False,  # required per mypy
)
