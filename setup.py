"""
Installs the pulsequantum package
"""

from setuptools import setup, find_packages
from pathlib import Path

import versioneer

readme_file_path = Path(__file__).absolute().parent / "README.md"

required_packages = ['opencensus-ext-azure',
                     'numpy',
                     'pandas',
                     # broadbean,
                     'PyQt5',
                     'matplotlib',
                     'broadbean @ git+https://github.com/QCoDeS/broadbean@master#egg=broadbean']
package_data = {"pulsequantum": ["conf/telemetry.ini"]}


setup(
    name="pulsequantum",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    python_requires=">=3.7",
    install_requires=required_packages,
    author="Rasmus Bjerregaard Christensen",
    author_email="rbcmail@gmail.com",
    description="Pulse building interface",
    long_description=readme_file_path.open().read(),
    long_description_content_type="text/markdown",
    license="",
    package_data=package_data,
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.7",
    ],
)
