import cx_Freeze

executables = [cx_Freeze.Executable("map2.py")]

cx_Freeze.setup(
    name="test game",
    options={"build_exe": {"packages":["pygame", "tones", "prompt_toolkit"],
                           "include_files":["audio/"]}},
    executables = executables
)