import cx_Freeze

exe_options = {
    "build_exe": {
        "packages": ["pygame", "tones", "prompt_toolkit"],
        "include_files": ["audio/"],
        "excludes": ["tkinter", "numpy", "scipy", "PyQt5", "distutils",
			"unittest", "test", "email", "pkg_resources"]
    }
}

exes = [cx_Freeze.Executable("example_map.py")]

cx_Freeze.setup(name="test game", options=exe_options, executables=exes)
