from pathlib import Path
from datetime import datetime
import shutil

HOME = Path.home()
CONFIG_DIR = HOME / "BlackStack" / "WachterEID" / "config"
TOOL_MANIFEST = CONFIG_DIR / "tool_manifest.yaml"
LICENSE_MANIFEST = CONFIG_DIR / "license_manifest.yaml"

SNAPSHOT_ROOT = HOME / "BlackStack" / "WachterEID" / "audit" / "snapshots"

def snapshot_manifests():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    snapshot_dir = SNAPSHOT_ROOT / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    tool_dest = snapshot_dir / "tool_manifest.yaml"
    license_dest = snapshot_dir / "license_manifest.yaml"

    shutil.copy2(TOOL_MANIFEST, tool_dest)
    shutil.copy2(LICENSE_MANIFEST, license_dest)

    print(f"[✓] Snapshot created at {snapshot_dir}")

if __name__ == "__main__":
    snapshot_manifests()
