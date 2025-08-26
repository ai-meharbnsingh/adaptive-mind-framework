# -*- coding: utf-8 -*-
# Your other imports/code follow...

import sys
import os

# Add the project root to the sys.path so Python can find prepare_session_context
# This simulates how it would be run or imported if it were a module
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    from scripts.prepare_session_context import validate_phase_num
    print("SUCCESS: 'validate_phase_num' can be imported.")
    # You can even try calling it to see if it works
    # print(f"Test validate_phase_num(0): {validate_phase_num(0)}")
except ImportError as e:
    print(f"FAILURE: Could not import 'validate_phase_num'. ImportError: {e}")
except NameError as e:
    print(f"FAILURE: 'validate_phase_num' is not defined after import. NameError: {e}")
except Exception as e:
    print(f"FAILURE: An unexpected error occurred: {e}")

# Also try to import the whole script and inspect its contents
try:
    import scripts.prepare_session_context as ps_context
    if hasattr(ps_context, 'validate_phase_num'):
        print("SUCCESS: 'validate_phase_num' found as an attribute of the imported module.")
    else:
        print("FAILURE: 'validate_phase_num' NOT found as an attribute of the imported module.")
except Exception as e:
    print(f"FAILURE: Could not import prepare_session_context module. Error: {e}")