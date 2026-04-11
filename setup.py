"""
setup.py — Run this FIRST before main.py
==========================================
Uses SUMO's netconvert tool to build the road network file
from our hand-crafted nodes and edges XML files.

HOW TO RUN:
    cd D:\sumo_project
    python setup.py
"""

import subprocess
import sys
import os

print("=" * 55)
print("  SUMO Network Generator")
print("=" * 55)

# -------------------------------------------------------
# Step 1: Check SUMO_HOME is set
# -------------------------------------------------------
sumo_home = os.environ.get("SUMO_HOME")
if not sumo_home:
    print("\n[ERROR] SUMO_HOME environment variable is NOT set.")
    print("  Fix: Add SUMO_HOME to your Windows environment variables.")
    print("  Example: SUMO_HOME = C:\\Program Files (x86)\\Eclipse\\Sumo")
    sys.exit(1)

print(f"\n[OK] SUMO_HOME = {sumo_home}")

# -------------------------------------------------------
# Step 2: Check input files exist
# -------------------------------------------------------
required_files = ["nodes.nod.xml", "edges.edg.xml"]
for f in required_files:
    if not os.path.exists(f):
        print(f"\n[ERROR] Missing file: {f}")
        print("  Make sure you are running this from D:\\sumo_project\\")
        sys.exit(1)
    print(f"[OK] Found: {f}")

# -------------------------------------------------------
# Step 3: Run netconvert to build the network
# -------------------------------------------------------
print("\n[RUNNING] netconvert ...")

cmd = [
    "netconvert",
    "--node-files",    "nodes.nod.xml",   # Our junction definitions
    "--edge-files",    "edges.edg.xml",   # Our road segment definitions
    "--output-file",   "my_network.net.xml",  # Output network file
    "--tls.guess",     "true",            # Auto-detect traffic light junctions
    "--tls.default-type", "static",       # Use simple fixed-time TLS programs
    "--no-turnarounds","true",            # No U-turns (cleaner logic)
    "--no-warnings",   "true",            # Suppress minor warnings
    "--offset.disable-normalization", "true"  # Keep our coordinate system as-is
]

result = subprocess.run(cmd, capture_output=True, text=True)

# Show any errors
if result.stderr.strip():
    print("\n[netconvert output]:")
    print(result.stderr.strip())

if result.returncode != 0:
    print("\n[ERROR] netconvert failed! Check output above.")
    print("Tip: Make sure 'netconvert' is on your PATH (it's in SUMO's bin folder).")
    sys.exit(1)

# -------------------------------------------------------
# Step 4: Verify output file was created
# -------------------------------------------------------
if os.path.exists("my_network.net.xml"):
    size_kb = os.path.getsize("my_network.net.xml") / 1024
    print(f"\n[SUCCESS] my_network.net.xml created! ({size_kb:.1f} KB)")
else:
    print("\n[ERROR] my_network.net.xml was NOT created. Something went wrong.")
    sys.exit(1)

print("\n" + "=" * 55)
print("  Setup complete!")
print("  Next step: python main.py")
print("=" * 55)