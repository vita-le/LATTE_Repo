# tests/test_cpacs_loading.py
def test_cpacs_opens(cpacs_case):
    # The fixture calls open_cpacs(): if TiGL cannot open the file, the test errors
    path, tigl, tixi = cpacs_case
    assert tigl is not None
    assert tixi is not None