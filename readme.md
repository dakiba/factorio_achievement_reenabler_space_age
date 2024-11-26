# Factorio Achievements Re-Enabler

A Python script to re-enable achievements in your Factorio save files by patching specific flags.

## Features

- Scans and patches `level.dat` files within a Factorio save.
- Searches for patterns associated with disabled achievements (`cheat-will-disable`, `editor`, `command-ran`).
- Dry-run mode for previewing changes without modifying files.
- Automatically creates backups before applying patches.

## Usage

```bash
python factorio_achievements_reenabler.py /path/to/your/save.zip [--patch]
```

### Arguments

- `/path/to/your/save.zip`: Path to your Factorio save file (usually a `.zip` file).
- `--patch`: Apply the patch to the save file. If omitted, the script runs in dry-run mode.

### Example

**Dry-run mode (default):**

```bash
python factorio_achievements_reenabler.py ~/Factorio/saves/my_save.zip
```

**Apply patch:**

```bash
python factorio_achievements_reenabler.py ~/Factorio/saves/my_save.zip --patch
```

## How It Works

1. **Extraction:** Extracts your save file to a temporary directory.
2. **Scanning:** Searches for `level.dat` files containing flags that disable achievements.
3. **Pattern Matching:** Looks for specific byte patterns and outputs hex dumps for debugging.
4. **Patching:** Modifies the necessary bytes to re-enable achievements (when `--patch` is used).
5. **Backup & Repackaging:** Backs up the original save and repackages the modified save.
6. **Cleanup:** Removes temporary files and directories after completion.

## Safety Precautions

- **Automatic Backup:** The script backs up your original save file with a `.bak` extension.
- **Dry-Run Mode:** Preview changes without modifying any files by default.
- **Recommendation:** Manually back up your save files before running the script.

## License

This project is licensed under the MIT License.

---

Feel free to customize and extend this script according to your needs.
