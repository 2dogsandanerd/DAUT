from setuptools import setup, find_packages

setup(
    name="daut",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "python-magic",
        "markdownify",
        "requests",
        "pydantic",
        "PyYAML",
        "chromadb>=0.4.0",
        "langchain>=0.0.300",
        "langchain-ollama>=0.3.1",
        "ollama>=0.1.7"
    ],
    entry_points={
        "console_scripts": [
            "daut=src.docs_updater:main",
        ],
    },
)