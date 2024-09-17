#!/usr/bin/env python3

import sys
import re
import os
from datetime import datetime

def main():
    if len(sys.argv) != 4:
        print("Usage: update_kernel_package.py <debian_directory> <kernel_version> <commit_id>")
        sys.exit(1)

    debian_dir = sys.argv[1]
    kernel_version = sys.argv[2]
    new_commit_id = sys.argv[3]

    # Check if debian_dir is a valid directory
    if not os.path.isdir(debian_dir):
        print(f"Error: '{debian_dir}' is not a valid directory.")
        sys.exit(1)

    # Paths to files
    changelog_file = os.path.join(debian_dir, 'changelog')
    rules_file = os.path.join(debian_dir, 'rules')
    control_file = os.path.join(debian_dir, 'control')

    # Check if the required files exist
    required_files = {
        'changelog': changelog_file,
        'rules': rules_file,
        'control': control_file
    }
    for name, file_path in required_files.items():
        if not os.path.isfile(file_path):
            print(f"Error: Required file '{file_path}' does not exist.")
            sys.exit(1)

    updated_files = []

    # Step 1: Get the old commit ID, kernel release, and Debian revision from debian/changelog
    old_commit_id = None
    old_kernelrelease = None
    old_debian_revision = None

    with open(changelog_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            # Find the latest entry
            if line.startswith('ti-linux-kernel'):
                # Extract the old version
                m = re.match(r'ti-linux-kernel \(([^)]+)\)', line)
                if m:
                    old_version = m.group(1)
                    # Split the version into kernel release and Debian revision
                    if '-' in old_version:
                        old_kernelrelease, old_debian_revision = old_version.rsplit('-', 1)
                    else:
                        old_kernelrelease = old_version
                        old_debian_revision = '1'  # Default to 1 if not specified
                else:
                    print("Error: Unable to parse version from changelog.")
                    sys.exit(1)
                # Now look for the commit ID in the next few lines
                for j in range(i+1, len(lines)):
                    if 'Build based on commit' in lines[j]:
                        # Extract old commit ID
                        m = re.search(r'Build based on commit (\w+)', lines[j])
                        if m:
                            old_commit_id = m.group(1)
                        else:
                            print("Error: Unable to parse old commit ID from changelog.")
                            sys.exit(1)
                        break
                if old_commit_id is None:
                    print("Error: Unable to find old commit ID in changelog.")
                    sys.exit(1)
                break

    if old_commit_id is None or old_kernelrelease is None:
        print("Error: Unable to find old commit ID or kernel release in changelog.")
        sys.exit(1)

    # Construct new kernel release
    new_kernelrelease = f"{kernel_version}+{new_commit_id}"

    # Increment Debian revision number
    try:
        debian_revision_number = int(old_debian_revision) + 1
    except ValueError:
        print("Error: Unable to parse Debian revision number.")
        sys.exit(1)

    new_debian_revision = str(debian_revision_number)

    # Full new version
    new_version = f"{new_kernelrelease}-{new_debian_revision}"

    # Step 2: Update debian/rules
    with open(rules_file, 'r') as f:
        rules_content = f.read()

    new_rules_content = rules_content.replace(old_kernelrelease, new_kernelrelease)
    if new_rules_content != rules_content:
        with open(rules_file, 'w') as f:
            f.write(new_rules_content)
        updated_files.append(rules_file)
    else:
        print("Warning: No changes made to debian/rules.")

    # Step 3: Update debian/control
    with open(control_file, 'r') as f:
        control_content = f.read()

    new_control_content = control_content.replace(old_kernelrelease, new_kernelrelease)
    if new_control_content != control_content:
        with open(control_file, 'w') as f:
            f.write(new_control_content)
        updated_files.append(control_file)
    else:
        print("Warning: No changes made to debian/control.")

    # Step 4: Update debian/changelog
    # Prepare the new changelog entry
    timestamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    new_entry_header = f"ti-linux-kernel ({new_version}) UNRELEASED; urgency=medium\n\n"
    new_entry_changes = f"  * Build based on commit {new_commit_id}\n"
    new_entry_footer = f"\n -- Nate Drude <nate.d@variscite.com>  {timestamp}\n\n"

    new_changelog_entry = new_entry_header + new_entry_changes + new_entry_footer

    # Prepend the new changelog entry to debian/changelog
    with open(changelog_file, 'r') as f:
        changelog_content = f.read()

    if new_changelog_entry.strip() not in changelog_content:
        with open(changelog_file, 'w') as f:
            f.write(new_changelog_entry + changelog_content)
        updated_files.append(changelog_file)
    else:
        print("Warning: New changelog entry already exists.")

    # Print success message
    if updated_files:
        print("Successfully updated the following files:")
        for filename in updated_files:
            print(f"- {filename}")
    else:
        print("No files were updated.")

if __name__ == "__main__":
    main()
