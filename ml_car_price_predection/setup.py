from setuptools import setup, find_packages

setup(
    name="car-price-prediction",
    version="1.0.0",
    author="ML Team",
    author_email="mailtopprakash01@gmail.com",
    description="Production ML pipeline for car price prediction",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.2.0",
        "mlflow>=2.6.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "streamlit>=1.22.0",
        "psycopg2-binary>=2.9.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pylint>=2.17.0",
            "isort>=5.12.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "train-model=src.pipelines.training_pipeline:main",
            "run-inference=src.pipelines.inference_pipeline:main",
        ]
    },
)
