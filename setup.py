from distutils.core import setup
import fnmatch, os.path
from libpathod import version

def _fnmatch(name, patternList):
    for i in patternList:
        if fnmatch.fnmatch(name, i):
            return True
    return False


def _splitAll(path):
    parts = []
    h = path
    while 1:
        if not h:
            break
        h, t = os.path.split(h)
        parts.append(t)
    parts.reverse()
    return parts


def findPackages(path, dataExclude=[]):
    """
        Recursively find all packages and data directories rooted at path. Note
        that only data _directories_ and their contents are returned -
        non-Python files at module scope are not, and should be manually
        included.

        dataExclude is a list of fnmatch-compatible expressions for files and
        directories that should not be included in pakcage_data.

        Returns a (packages, package_data) tuple, ready to be passed to the
        corresponding distutils.core.setup arguments.
    """
    packages = []
    datadirs = []
    for root, dirs, files in os.walk(path, topdown=True):
        if "__init__.py" in files:
            p = _splitAll(root)
            packages.append(".".join(p))
        else:
            dirs[:] = []
            if packages:
                datadirs.append(root)

    # Now we recurse into the data directories
    package_data = {}
    for i in datadirs:
        if not _fnmatch(i, dataExclude):
            parts = _splitAll(i)
            module = ".".join(parts[:-1])
            acc = package_data.get(module, [])
            for root, dirs, files in os.walk(i, topdown=True):
                sub = os.path.join(*_splitAll(root)[1:])
                if not _fnmatch(sub, dataExclude):
                    for fname in files:
                        path = os.path.join(sub, fname)
                        if not _fnmatch(path, dataExclude):
                            acc.append(path)
                else:
                    dirs[:] = []
            package_data[module] = acc
    return packages, package_data


long_description = open("README.txt").read()
packages, package_data = findPackages("libpathod")
setup(
        name = "pathod",
        version = version.VERSION,
        description = "A pathological HTTP/S daemon for testing and stressing clients.",
        long_description = long_description,
        author = "Aldo Cortesi",
        author_email = "aldo@corte.si",
        url = "http://pathod.net",
        packages = packages,
        package_data = package_data,
        scripts = ["pathod", "pathoc"],
        classifiers = [
            "License :: OSI Approved :: MIT License",
            "Development Status :: 5 - Production/Stable",
            "Operating System :: POSIX",
            "Programming Language :: Python",
            "Topic :: Internet",
            "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
            "Topic :: Software Development :: Testing",
            "Topic :: Software Development :: Testing :: Traffic Generation",
            "Topic :: Internet :: WWW/HTTP",
        ],
        install_requires=['netlib>=0.2.2', "requests>=1.0.4", "flask",
                          "six"],
)
