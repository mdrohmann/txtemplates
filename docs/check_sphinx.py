import py  # noqa
import subprocess


def test_linkcheck(tmpdir):
    doctrees = tmpdir.join("doctrees")
    htmldir = tmpdir.join("html")
    subprocess.check_call(
        ["sphinx-build", "-W", "-blinkcheck",
         "-d", str(doctrees), "source", str(htmldir)])


def test_build_docs(tmpdir):
    doctrees = tmpdir.join("doctrees")
    htmldir = tmpdir.join("html")
    subprocess.check_call([
        "sphinx-build", "-W", "-bhtml",
        "-d", str(doctrees), "source", str(htmldir)])
