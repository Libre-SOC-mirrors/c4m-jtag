from setuptools import setup, find_packages


def scm_version():
    def local_scheme(version):
        if version.tag and not version.distance:
            return version.format_with("")
        else:
            return version.format_choice("+{node}", "+{node}.dirty")
    return {
        "relative_to": __file__,
        "version_scheme": "guess-next-dev",
        "local_scheme": local_scheme
    }


setup(
    name="c4m_jtag",
    use_scm_version=scm_version(),
    author="Staf Verhaegen",
    author_email="staf@fibraservi.eu",
    description="",
    license="multi",
    python_requires="~=3.6",
    setup_requires=["setuptools_scm"],

    # removing cocotb, causing unnecessary dependency and install problems
    install_requires=["setuptools", "nmigen", "nmigen-soc", "modgrammar"],

    # unit tests require cocotb: main operation does not
    tests_require=['cocotb'],

    include_package_data=True,
    packages=find_packages(),
    project_urls={
        #"Documentation": "???",
        "Source Code": "https://gitlab.com/Chips4Makers/c4m-jtag",
        "Bug Tracker": "https://gitlab.com/Chips4Makers/c4m-jtag/issues",
    },
)
