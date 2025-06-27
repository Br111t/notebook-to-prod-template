import os
import sys
import asyncio

# 1) Enable Jupyter’s new platformdirs paths (silences the DeprecationWarning)
os.environ.setdefault("JUPYTER_PLATFORM_DIRS", "1")

# 2) On Windows, switch to the SelectorEventLoop
# (avoids the zmq Proactor warning)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
