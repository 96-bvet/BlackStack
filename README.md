# BlackStack Sentinel Core

This repository contains the core components of the BlackStack Sentinel system, including the main Sentinel executable, persona management scripts, and auxiliary tools.

## Structure
- `sentinel_core.py`: Main Sentinel executable.
- `persona_*`: Persona management scripts.
- `mutation_log.json`: Log of mutations applied to the Sentinel codebase.
- `approval_queue.json`: Queue of files awaiting approval for integration into the unified Sentinel architecture.

## Usage
To initialize the Sentinel system, run `sentinel_core.py` with the appropriate flags.

### Flags
- `--finalize`: Run unified Sentinel finalization now.
- `--finalize-queue`: Finalize and stitch together all files currently in the approval queue.

---

### Note
This is a highly experimental setup and should be used with caution. Ensure backups are in place before proceeding with any operations that modify the codebase.
