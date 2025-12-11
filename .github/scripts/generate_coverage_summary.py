#!/usr/bin/env python3
"""Generate coverage summary from merged XML file."""

import xml.etree.ElementTree as ET
import sys
import os

xml_file = os.environ.get('COVERAGE_XML', 'coverage-merged.xml')
summary_file = os.environ.get('SUMMARY_FILE', 'coverage-summary.txt')
test_type = os.environ.get('TEST_TYPE', 'Tests')

try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    rate = float(root.get('line-rate', 0)) * 100
    lines_covered = int(root.get('lines-covered', 0))
    lines_valid = int(root.get('lines-valid', 0))
    with open(summary_file, 'w') as f:
        f.write(f"{test_type} Coverage: {rate:.2f}%\n")
        f.write(f"Lines covered: {lines_covered}/{lines_valid}\n")
    print(f"✓ Generated summary: {rate:.2f}% coverage")
except Exception as e:
    print(f"⚠️  Failed to generate summary: {e}")
    with open(summary_file, 'w') as f:
        f.write("No coverage data available\n")

