import os
import zipfile
import shutil
import zlib
import sys
import argparse

def extract_save_file(save_path):
    extract_dir = os.path.join(os.path.dirname(save_path), os.path.splitext(os.path.basename(save_path))[0])
    print(f"Extracting save file to: {extract_dir}")
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir

def find_level_dat_files(extract_dir):
    level_dat_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.startswith('level.dat') and not file.endswith('.datmetadata') and not file.endswith('.bin'):
                level_dat_files.append(os.path.join(root, file))
    return level_dat_files

def hex_dump(data, start, end):
    print("Offset(h)  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII")
    print("--------  -----------------------------------------------  ----------------")
    for i in range(start, end, 16):
        chunk = data[i:i+16]
        hex_values = ' '.join(f"{byte:02X}" for byte in chunk)
        ascii_values = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in chunk)
        print(f"{i:08X}  {hex_values:<47}  {ascii_values}")

def process_level_dat_file(file_path, patterns, do_patch):
    with open(file_path, 'rb') as f:
        compressed_data = f.read()

    try:
        data = zlib.decompress(compressed_data)
    except zlib.error as e:
        print(f"Error decompressing file {file_path}: {e}")
        return False

    data_modified = False

    for pattern in patterns:
        search_string = pattern['search_string']
        index = 0

        while True:
            index = data.find(search_string, index)
            if index == -1:
                break  # No more occurrences

            print(f"\nFound '{search_string.decode()}' at index {index} in file {file_path}")

            # Search backwards up to specified bytes for FF sequence
            search_start = max(0, index - pattern['search_back_bytes'])
            ff_sequence = pattern['ff_sequence']
            ff_index = data.rfind(ff_sequence, search_start, index)

            if ff_index == -1:
                print(f"Could not find FF x{len(ff_sequence)} sequence before '{search_string.decode()}'.")
                # Even if FF sequence not found, output hex dump
                dump_start = max(0, index - 250)
                dump_end = min(len(data), index + 250)
                print("\nHex dump around search string (FF sequence not found):")
                hex_dump(data, dump_start, dump_end)
                index += len(search_string)
                continue  # Move to next occurrence

            print(f"Found FF x{len(ff_sequence)} sequence at index {ff_index}")

            # Calculate target index
            target_index = ff_index + pattern['ff_sequence_offset']
            if target_index < 0 or target_index >= len(data):
                print("Target index out of bounds, skipping this occurrence.")
                index += len(search_string)
                continue

            # Hex dump around target_index
            dump_start = max(0, target_index - 250)
            dump_end = min(len(data), target_index + 250)
            print("\nHex dump around target index:")
            hex_dump(data, dump_start, dump_end)

            # Change byte from 0x01 to 0x00 if it is 0x01
            original_byte = data[target_index]
            if original_byte == 0x01:
                print(f"\nByte at index {target_index} is 0x01")
                if do_patch:
                    print(f"Changing byte at index {target_index} from 0x01 to 0x00")
                    data = data[:target_index] + b'\x00' + data[target_index + 1:]
                    data_modified = True
                else:
                    print(f"Would change byte at index {target_index} from 0x01 to 0x00 (dry run)")
            else:
                print(f"Byte at index {target_index} is 0x{original_byte:02X}, not 0x01, skipping.")

            index += len(search_string)

    if data_modified and do_patch:
        # Compress the modified data
        compressed_data_fixed = zlib.compress(data)
        # Write the patched data back to the file
        with open(file_path, 'wb') as f:
            f.write(compressed_data_fixed)
        print(f"Patched file: {file_path}")
        return True
    else:
        print(f"No modifications made to file: {file_path}")
        return False

def backup_and_create_new_save(save_path, extract_dir):
    # Backup the original save file
    print("Backing up original save file")
    backup_path = save_path + '.bak'
    shutil.move(save_path, backup_path)

    # Create a new save file
    print("Creating new save file")
    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(extract_dir, zipf)

    # Clean up the extracted directory
    print("Cleaning up")
    shutil.rmtree(extract_dir)
    print("Done")

def zipdir(path, ziph):
    # Zip the directory contents
    for root, dirs, files in os.walk(path):
        for file in files:
            abs_file = os.path.join(root, file)
            rel_path = os.path.relpath(abs_file, path)
            ziph.write(abs_file, arcname=rel_path)

def main(save_path, do_patch):
    # Prompt the user for the save file path
    if not save_path:
        save_path = input("Enter the path to the save file: ").strip('"')

    extract_dir = extract_save_file(save_path)
    level_dat_files = find_level_dat_files(extract_dir)

    # Define the patterns to search and their associated parameters
    patterns = [
        {
            'name': 'cheat-will-disable',
            'search_string': b'cheat-will-disable',
            'search_back_bytes': 100,
            'ff_sequence': b'\xFF' * 16,
            'ff_sequence_offset': -3,  # Offset from FF sequence to target byte
        },
        {
            'name': 'editor-will-disable',
            'search_string': b'editor',
            'search_back_bytes': 300,
            'ff_sequence': b'\x01' + b'\xFF' * 8,
            'ff_sequence_offset': -1,  # May need adjustment
        },
        {
            'name': 'command-ran',
            'search_string': b'command-ran',
            'search_back_bytes': 300,
            'ff_sequence': b'\x01' + (b'\xFF' * 8),
            'ff_sequence_offset': 0,  # May need adjustment
        },
        # You can add more patterns here
    ]

    data_modified = False

    # Process each 'level.dat' file
    for file_path in level_dat_files:
        modified = process_level_dat_file(file_path, patterns, do_patch)
        if modified:
            data_modified = True

    if do_patch and data_modified:
        backup_and_create_new_save(save_path, extract_dir)
    else:
        print("No changes made. Cleaning up extracted directory.")
        shutil.rmtree(extract_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Patch Factorio save file to re-enable achievements.')
    parser.add_argument('save_file', nargs='?', help='Path to the save file')
    parser.add_argument('--patch', action='store_true', help='Apply the patch to the save file')
    args = parser.parse_args()

    main(args.save_file, args.patch)
