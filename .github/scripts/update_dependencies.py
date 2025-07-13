#!/usr/bin/env python3
import requests
import yaml
import re
import hashlib
import sys
import os
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime

PACKAGES = {
    'bubblewrap': 'https://archive.archlinux.org/packages/b/bubblewrap/',
    'krb5': 'https://archive.archlinux.org/packages/k/krb5/',
    'keyutils': 'https://archive.archlinux.org/packages/k/keyutils/',
    'libtorrent-rasterbar': 'https://archive.archlinux.org/packages/l/libtorrent-rasterbar/',
    'freedownloadmanager': 'https://debrepo.freedownloadmanager.org/pool/main/f/freedownloadmanager/'
}

def parse_version(pkg_name, filename):
    """Properly parse versions for all package types"""
    filename = unquote(filename)
    if pkg_name == 'freedownloadmanager':
        return filename.split('_')[1].split('_amd64.deb')[0]
    elif pkg_name == 'libtorrent-rasterbar':
        parts = filename.split('-')
        return f"{parts[2]}-{parts[3].replace('.pkg.tar.zst', '')}"
    else:
        parts = filename.split('-')
        return f"{parts[1]}-{parts[2].replace('.pkg.tar.zst', '')}"

def normalize_version(ver):
    """Normalize version string to comparable tuple (moved outside compare_versions)"""
    # Handle epoch (e.g., "1:2.0.11-4" -> epoch=1, rest="2.0.11-4")
    if ':' in ver:
        epoch, ver_part = ver.split(':', 1)
        epoch = int(epoch)
    else:
        epoch = 0
        ver_part = ver
    
    # Split version and release (e.g., "2.0.11-4" -> version="2.0.11", rel="4")
    if '-' in ver_part:
        version, rel = ver_part.split('-', 1)
    else:
        version = ver_part
        rel = '0'
    
    # Split version components (e.g., "2.0.11" -> [2, 0, 11])
    version_parts = []
    for part in version.split('.'):
        if part.isdigit():
            version_parts.append(int(part))
        else:
            version_parts.append(0)
    
    # Split release components (e.g., "4" -> [4])
    rel_parts = []
    for part in rel.split('.'):
        if part.isdigit():
            rel_parts.append(int(part))
        else:
            rel_parts.append(0)
    
    return (epoch, *version_parts, *rel_parts)

def compare_versions(current, latest):
    """Compare versions including pkgrel, handling epochs"""
    current_norm = normalize_version(current)
    latest_norm = normalize_version(latest)
    return current_norm >= latest_norm

def get_latest_pkg(package_name, base_url):
    """Get latest package version and SHA256"""
    try:
        print(f"\nChecking {package_name} at {base_url}")
        r = requests.get(base_url, timeout=10)
        r.raise_for_status()

        if package_name == 'freedownloadmanager':
            pattern = r'href="(freedownloadmanager_([\d.]+)_amd64\.deb)"'
        else:
            pattern = rf'href="({package_name}-([^"]+)-x86_64\.pkg\.tar\.zst)"'

        matches = re.findall(pattern, r.text)
        if not matches:
            print(f"No packages found for {package_name}")
            return None

        versions = []
        for file, _ in matches:
            try:
                ver = parse_version(package_name, file)
                versions.append((ver, file))
            except Exception as e:
                print(f"Error parsing version from {file}: {e}")
                continue

        if not versions:
            return None

        # Sort versions using our normalization function
        versions.sort(key=lambda x: normalize_version(x[0]))

        latest_ver, latest_file = versions[-1]
        pkg_url = f"{base_url}{latest_file}"

        print(f"Downloading {pkg_url} to verify SHA256...")
        r = requests.get(pkg_url, stream=True, timeout=30)
        r.raise_for_status()

        hasher = hashlib.sha256()
        for chunk in r.iter_content(1024):
            hasher.update(chunk)
        sha256 = hasher.hexdigest()

        print(f"Found version: {latest_ver}")
        print(f"SHA256: {sha256}")

        return {
            'version': latest_ver,
            'sha256': sha256,
            'url': pkg_url
        }

    except Exception as e:
        print(f"Error processing {package_name}: {str(e)}")
        return None

def update_metainfo(version):
    """Update the metainfo.xml file with new release information while preserving formatting"""
    metainfo_path = Path('org.freedownloadmanager.Manager.metainfo.xml')
    
    try:
        with open(metainfo_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        in_releases = False
        version_exists = False
        today = datetime.now().strftime('%Y-%m-%d')
        new_release_line = f'    <release version="{version}" date="{today}"/>\n'

        for line in lines:
            if '<releases>' in line:
                in_releases = True
                new_lines.append(line)
                # Add our new release right after the opening tag
                new_lines.append(new_release_line)
                continue
            elif '</releases>' in line:
                in_releases = False
                new_lines.append(line)
                continue
            elif in_releases and version in line:
                version_exists = True
                break
            
            new_lines.append(line)

        if version_exists:
            print(f"Version {version} already exists in metainfo.xml")
            return False

        # Write back to file with exact same formatting
        with open(metainfo_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"Updated metainfo.xml with new version {version}")
        return True
        
    except Exception as e:
        print(f"Error updating metainfo.xml: {str(e)}")
        return False

def update_manifest(manifest_path):
    changes = []
    metainfo_updated = False

    # Read the original file to preserve formatting
    with open(manifest_path, 'r') as f:
        original_lines = f.readlines()

    new_lines = []
    current_module = None
    latest_info = None

    for line in original_lines:
        # Detect module sections
        if line.strip().startswith('- name:'):
            current_module = line.split(':')[1].strip()
            new_lines.append(line)
            continue

        # Check for URL lines in the current module
        if current_module in ['bubblewrap', 'krb5', 'keyutils', 'libtorrent', 'fdm']:
            if 'url:' in line:
                pkg_name = {
                    'libtorrent': 'libtorrent-rasterbar',
                    'fdm': 'freedownloadmanager'
                }.get(current_module, current_module)

                if pkg_name in PACKAGES:
                    latest_info = get_latest_pkg(pkg_name, PACKAGES[pkg_name])
                    if latest_info:
                        # Find the current version from URL
                        current_url = line.split('url:')[1].strip()
                        current_ver = parse_version(pkg_name, current_url.split('/')[-1])

                        if not compare_versions(current_ver, latest_info['version']):
                            change = f"{current_module}: {current_ver} → {latest_info['version']}"
                            print(f"Update available: {change}")
                            changes.append(change)

                            # Update the URL line
                            new_url = latest_info['url']
                            new_lines.append(line.replace(current_url, new_url))
                            
                            # If this is FDM, update the metainfo.xml
                            if pkg_name == 'freedownloadmanager':
                                metainfo_updated = update_metainfo(latest_info['version'])
                            continue

            if 'sha256:' in line and latest_info:
                current_sha = line.split('sha256:')[1].strip()
                new_lines.append(line.replace(current_sha, latest_info['sha256']))
                latest_info = None  # Reset for next module
                continue

        # Keep the original line if no changes needed
        new_lines.append(line)

    if changes or metainfo_updated:
        # Write back the modified file with original formatting
        with open(manifest_path, 'w') as f:
            f.writelines(new_lines)
        print("\nManifest updated successfully!")
        # Write changes to GitHub environment file
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"CHANGES_MADE=true\n")
            f.write(f"CHANGES_DETAILS={'; '.join(changes)}\n")
        return True
    else:
        print("\nAll packages are up-to-date")
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write("CHANGES_MADE=false\n")
        return False

if __name__ == "__main__":
    manifest_path = Path('org.freedownloadmanager.Manager.yaml')
    update_manifest(manifest_path)
