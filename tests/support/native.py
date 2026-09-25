"""Stand-ins for the optional native package in backend-selection tests."""


def missing_module(name: str):
    """Raise what importing an absent module called ``name`` raises."""
    raise ModuleNotFoundError("module absent", name=name)
