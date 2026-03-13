"""Setup for photo-filter."""
from setuptools import setup, find_packages

setup(
    name="photo-filter",
    version="0.1.0",
    description="智能照片筛选工具",
    author="Photo Filter Team",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "PyYAML>=6.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "clip": ["torch>=2.0.0", "transformers>=4.30.0"],
    },
    entry_points={
        "console_scripts": [
            "photo-filter=photofilter.cli:main",
        ],
    },
    python_requires=">=3.9",
)
