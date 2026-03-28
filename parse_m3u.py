#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U Playlist Parser - Corrects channel categorization
Fixes: AF - prefixed general channels were incorrectly assigned to COMORRES
"""

import json
import re

def parse_m3u(filepath):
    """Parse M3U file and organize channels by country/category (ALL regions)"""

    channels_data = {
        "total_channels": 0,
        "regions": {}
    }

    current_section = None
    current_channels = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this is a section header
            if line.startswith('#EXTINF:0,##### '):
                # Save previous section
                if current_section and current_channels:
                    section_name = current_section.replace('AF - ', '').replace('C+ AFRICA - ', '').strip()
                    channels_data["regions"][section_name] = {
                        "count": len(current_channels),
                        "channels": current_channels
                    }
                    channels_data["total_channels"] += len(current_channels)

                # Extract section name
                match = re.search(r'##### (.+?) #####', line)
                if match:
                    section_text = match.group(1).strip()
                    # Start collecting channels for ANY section
                    current_section = section_text
                    current_channels = []
                    i += 1
                    continue

            # If we're in a section, collect channel info
            if current_section:
                # Channel name line
                if line.startswith('#EXTINF:0,') and not line.startswith('#EXTINF:0,#####'):
                    channel_name = line.replace('#EXTINF:0,', '').strip()
                    # Get the next line (URL)
                    if i + 1 < len(lines):
                        channel_url = lines[i + 1].strip()
                        if channel_url and not channel_url.startswith('#'):
                            current_channels.append({
                                "name": channel_name,
                                "url": channel_url
                            })
                            i += 2
                            continue

            i += 1

        # Don't forget the last section
        if current_section and current_channels:
            section_name = current_section.replace('AF - ', '').replace('C+ AFRICA - ', '').strip()
            channels_data["regions"][section_name] = {
                "count": len(current_channels),
                "channels": current_channels
            }
            channels_data["total_channels"] += len(current_channels)

        return channels_data

    except Exception as e:
        print(f"❌ Error parsing M3U: {e}")
        return channels_data

if __name__ == '__main__':
    print("🔄 Parsing M3U playlist...")
    data = parse_m3u('Playlist.m3u')

    # Save to JSON
    output_file = 'channels.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Parsing complete!")
    print(f"📊 Total channels: {data['total_channels']}")
    print(f"🌍 Categories: {len(data['regions'])}")
    print(f"\n📋 Channel counts per category:")
    for region in sorted(data['regions'].keys()):
        count = data['regions'][region]['count']
        print(f"   {region}: {count} channels")
    print(f"\n💾 Saved to {output_file}")
