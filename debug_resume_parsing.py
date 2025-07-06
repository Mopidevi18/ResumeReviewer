#!/usr/bin/env python3
"""
Debug script to analyze resume parsing and identify issues with project headings.
Usage: python debug_resume_parsing.py <path_to_resume.pdf>
"""

import sys
import json
from backend.utils.parse_resume import debug_parse_resume, split_bullets

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_resume_parsing.py <path_to_resume.pdf>")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    
    print(f"🔍 Analyzing resume: {resume_path}")
    print("=" * 60)
    
    try:
        debug_info = debug_parse_resume(resume_path)
        
        print("📋 SUMMARY:")
        print(f"  Total lines extracted: {len(debug_info['all_lines'])}")
        print(f"  Bold lines filtered: {len(debug_info['bold_lines'])}")
        print(f"  Heading lines filtered: {len(debug_info['heading_lines'])}")
        print(f"  Lines kept for processing: {len(debug_info['filtered_lines'])}")
        print(f"  Final bullets extracted: {len(debug_info['final_bullets'])}")
        
        print("\n🔥 BOLD LINES (filtered out):")
        for line in debug_info['bold_lines']:
            print(f"  • {line}")
        
        print("\n🏷️ HEADING LINES (filtered out by pattern detection):")
        for line in debug_info['heading_lines']:
            print(f"  • {line}")
        
        print("\n📝 FINAL BULLETS:")
        for i, bullet in enumerate(debug_info['final_bullets'], 1):
            print(f"  {i}. {bullet}")
        
        print("\n🔧 DETAILED ANALYSIS:")
        print("All lines with their classification:")
        for i, line_info in enumerate(debug_info['all_lines'], 1):
            status = "KEPT"
            if line_info['is_bold']:
                status = "FILTERED (bold)"
            elif line_info['text'] in debug_info['heading_lines']:
                status = "FILTERED (heading)"
            
            print(f"  {i:2d}. [{status:16s}] {line_info['text']}")
        
        # Check for potential issues
        print("\n⚠️  POTENTIAL ISSUES:")
        issues_found = False
        
        # Check if any bullets contain project-like names
        for bullet in debug_info['final_bullets']:
            if any(keyword in bullet.lower() for keyword in ['project', 'system', 'platform', 'application', 'tool', 'tracker']):
                if len(bullet.split()) <= 6 and not bullet.endswith('.'):
                    print(f"  • Possible project heading in bullets: '{bullet}'")
                    issues_found = True
        
        # Check if any kept lines look like headings
        for line in debug_info['filtered_lines']:
            if line.strip() and len(line.split()) <= 3 and line.strip().istitle():
                print(f"  • Possible heading in kept lines: '{line}'")
                issues_found = True
        
        if not issues_found:
            print("  No obvious issues detected!")
        
    except Exception as e:
        print(f"❌ Error analyzing resume: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 