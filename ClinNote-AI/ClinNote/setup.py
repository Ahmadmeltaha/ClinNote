"""
ClinNote package setup.
Allows 'pip install -e .' from the project root for clean imports.
"""

from setuptools import setup, find_packages

setup(
    name="clinnote",
    version="0.1.0",
    description="AI-Driven Clinical Data Integration Platform (Capstone 2)",
    author="Ahmad Jaber, Daliah Qadri",
    packages=find_packages(where="."),
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "h5py>=3.8.0",
        "tqdm>=4.65.0",
    ],
)
