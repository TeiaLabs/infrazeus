from __future__ import annotations

from pathlib import Path

import setuptools


def read_multiline_as_list(file_path: str) -> list[str]:
    with open(file_path) as fh:
        contents = fh.read().split("\n")
        if contents[-1] == "":
            contents.pop()
        return contents

requirements = read_multiline_as_list("requirements.txt")


setuptools.setup(
    name="infrazeus",
    version="0.1.0",
    author="Teialabs",
    author_email="contato@teialabs.com",
    description="Teia Infra package",
    url="https://github.com/TeiaLabs/infrazeus/",
    packages=setuptools.find_packages(),
    python_requires=">=3.11",
    install_requires=requirements,
)
