def main():
    """Entry point for the hammurabi CLI."""
    import sys
    import os

    # Get the root directory containing hammurabi.py
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hammurabi_script = os.path.join(root_dir, "hammurabi.py")

    # Execute the root hammurabi.py script
    with open(hammurabi_script) as f:
        code = compile(f.read(), hammurabi_script, "exec")
        exec(code, {"__name__": "__main__", "__file__": hammurabi_script})
