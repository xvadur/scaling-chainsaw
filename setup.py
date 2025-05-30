from setuptools import setup, find_packages

setup(
    name="aetheros_protocol",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain==0.0.27",
        "requests==2.31.0",
        "pyyaml==6.0.1",
        "python-dotenv==1.0.0",
        "jsonschema==4.17.3",
        "docker==6.1.2",
        "fastapi==0.95.0",
        "uvicorn==0.21.0",
        "pytest==7.3.1",
        "pytest-asyncio==0.21.0",
        "prometheus-client==0.16.0",
        "jinja2==3.1.2",
        "psutil==5.9.0",
        "networkx==3.1",
    ],
    python_requires=">=3.8",
)
