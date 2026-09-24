from tixi3 import tixi3wrapper
from tigl3 import tigl3wrapper

CPACS_FILE = "examples/GripenECPACS.xml"

# Apriamo il file con TIXI (livello XML basso)
tixi_h = tixi3wrapper.Tixi3()
tixi_h.open(CPACS_FILE)

# Apriamo la configurazione con TIGL (livello geometrico)
tigl_h = tigl3wrapper.Tigl3()
tigl_h.open(tixi_h, "")

print("=== Metodi disponibili relativi a 'wing' ===")
for name in dir(tigl_h):
    if "wing" in name.lower() or "Wing" in name:
        print(name)

print("\n=== Metodi disponibili relativi a nome/uid/aircraft ===")
for name in dir(tigl_h):
    if "name" in name.lower() or "uid" in name.lower() or "aircraft" in name.lower():
        print(name)