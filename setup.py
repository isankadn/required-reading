from setuptools import find_packages, setup

setup(
    name="required-reading",
    version="0.1.0",
    description="Standalone Django app for required reading PDFs and acknowledgements.",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["Django>=3.2"],
    entry_points={
        "lms.djangoapp": [
            "required_reading = required_reading.apps:RequiredReadingConfig",
        ],
    },
    python_requires=">=3.8",
)
