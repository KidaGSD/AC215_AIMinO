#!/usr/bin/env python3
"""Merge multiple coverage XML files into a single XML file."""

import xml.etree.ElementTree as ET
import sys
import os
import time

xml_files_str = os.environ.get('XML_FILES', '')
xml_files = xml_files_str.split() if xml_files_str else []
if not xml_files:
    print("No XML files to merge")
    sys.exit(1)

all_packages = {}
total_lines = 0
total_covered = 0

for xml_file in xml_files:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        line_rate = float(root.get('line-rate', 0))
        lines_valid = int(root.get('lines-valid', 0))
        lines_covered = int(root.get('lines-covered', 0))
        total_lines += lines_valid
        total_covered += lines_covered
        for package in root.findall('.//package'):
            pkg_name = package.get('name', '')
            if pkg_name not in all_packages:
                all_packages[pkg_name] = package
    except Exception as e:
        print(f"Warning: Failed to parse {xml_file}: {e}")

merged_root = ET.Element('coverage')
if total_lines > 0:
    merged_rate = total_covered / total_lines
else:
    merged_rate = 0.0

merged_root.set('line-rate', str(merged_rate))
merged_root.set('branch-rate', '0')
merged_root.set('lines-covered', str(total_covered))
merged_root.set('lines-valid', str(total_lines))
merged_root.set('branches-covered', '0')
merged_root.set('branches-valid', '0')
merged_root.set('complexity', '0')
merged_root.set('version', '7.13.0')
merged_root.set('timestamp', str(int(time.time() * 1000)))

ET.SubElement(merged_root, 'sources')
packages_elem = ET.SubElement(merged_root, 'packages')
for pkg_name, pkg_elem in all_packages.items():
    packages_elem.append(pkg_elem)

output_file = os.environ.get('OUTPUT_FILE', 'coverage-merged.xml')
tree = ET.ElementTree(merged_root)
tree.write(output_file, encoding='utf-8', xml_declaration=True)
print(f"✓ Merged {len(xml_files)} XML files")
print(f"  Coverage: {merged_rate * 100:.2f}%")
print(f"  Output: {output_file}")

