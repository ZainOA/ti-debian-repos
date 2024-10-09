#!/usr/bin/env python3

import sys
import re
import os
from datetime import datetime

def main():
    if len(sys.argv) != 5:
        print("Usage: update_kernel_package.py <debian_directory> <kernel_version> <commit_id> <author>")
        sys.exit(1)

    debian_dir = sys.argv[1]
    kernel_version = sys.argv[2]
    new_commit_id = sys.argv[3]
    author = sys.argv[4]

    # Paths to files
    changelog_file = os.path.join(debian_dir, 'changelog')
    rules_file = os.path.join(debian_dir, 'rules')
    control_file = os.path.join(debian_dir, 'control')

    # Read the old version from debian/changelog
    with open(changelog_file, 'r') as f:
        for line in f:
            if line.startswith('ti-linux-kernel'):
                m = re.match(r'ti-linux-kernel \(([^)]+)\)', line)
                if m:
                    old_version = m.group(1)
                    break
        else:
            print("Error: Could not find version in changelog.")
            sys.exit(1)

    # Parse the old version
    version_regex = r'(?P<kernel_version>[^-]+)-var(?P<var_number>\d+)\+(?P<commit_id>[^-]+)-(?P<debian_revision>.+)'
    m = re.match(version_regex, old_version)
    if not m:
        print(f"Error: Could not parse old version '{old_version}'.")
        sys.exit(1)

    old_kernel_version = m.group('kernel_version')
    old_var_number = int(m.group('var_number'))
    old_debian_revision = m.group('debian_revision')

    # Determine new var number
    if old_kernel_version == kernel_version:
        new_var_number = old_var_number + 1
    else:
        new_var_number = 1

    # Build new version
    new_version = f"{kernel_version}-var{new_var_number}+{new_commit_id}-{old_debian_revision}"

    # Update rules and control files
    files_to_update = [rules_file, control_file]
    for filename in files_to_update:
        with open(filename, 'r') as f:
            content = f.read()

        content_updated = content

        # Update version strings
        content_updated = content_updated.replace(old_version, new_version)
        if old_kernel_version != kernel_version:
            content_updated = content_updated.replace(old_kernel_version, kernel_version)

        # if filename == rules_file:
        #     # Update KERNELRELEASE
        #     content_updated = re.sub(
        #         r'(KERNELRELEASE=)[^\s]+',
        #         rf'\g<1>{kernel_version}-k3-var',
        #         content_updated
        #     )
        #     # Add LOCALVERSION with commit ID
        #     content_updated = re.sub(
        #         r'(KBUILD_BUILD_VERSION=\d+)',
        #         rf'\g<1> LOCALVERSION=+{new_commit_id}',
        #         content_updated
        #     )

        if filename == control_file:
            # Replace the Maintainer line
            content_updated = re.sub(
                r'^Maintainer:.*$', f'Maintainer: {author}', content_updated, flags=re.MULTILINE
            )

        if content != content_updated:
            with open(filename, 'w') as f:
                f.write(content_updated)
            print(f"Updated {filename}")
        else:
            print(f"No changes made to {filename}.")

    # Update debian/changelog
    timestamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    new_changelog_entry = (
        f"ti-linux-kernel ({new_version}) UNRELEASED; urgency=medium\n\n"
        f"  * Build based on commit {new_commit_id}\n\n"
        f" -- {author}  {timestamp}\n\n"
    )

    with open(changelog_file, 'r') as f:
        changelog_content = f.read()

    with open(changelog_file, 'w') as f:
        f.write(new_changelog_entry + changelog_content)
    print(f"Updated {changelog_file}")

if __name__ == "__main__":
    main()
