#!/usr/bin/env python3
"""
Script to find occurrences of "8051" in all files in a directory tree.
This helps identify where the incorrect port number is defined.
"""

import os
import re
import argparse
from pathlib import Path
import sys

def find_port_references(search_dir, search_text='8051', file_extensions=None, show_context=True):
    """
    Search for occurrences of a port number in files.
    
    Args:
        search_dir (str): Directory to search in
        search_text (str): Text to search for (default: '8051')
        file_extensions (list): File extensions to search in (default: all files)
        show_context (bool): Whether to show the line containing the match
        
    Returns:
        dict: Dictionary of {filename: [list of matches]}
    """
    search_dir = Path(search_dir).expanduser().resolve()
    
    # Dictionary to store results
    results = {}
    
    # Convert search_text to a regex pattern to find both string and numeric occurrences
    # This handles cases like '8051', "8051", 8051, localhost:8051, etc.
    pattern = re.compile(r'[^0-9]{}[^0-9]'.format(search_text))
    
    # Set default file_extensions if not provided
    if file_extensions is None:
        file_extensions = ['.py', '.js', '.json', '.yaml', '.yml', '.env', '.sh', '.conf', '.txt', '.md', '.html', '.css']
    
    print(f"Searching for '{search_text}' in {search_dir}...")
    print(f"File extensions: {', '.join(file_extensions)}")
    
    try:
        # Walk through all files in the directory
        for root, _, files in os.walk(search_dir):
            for filename in files:
                file_path = Path(root) / filename
                
                # Skip if file extension is not in the list
                if file_extensions and not any(file_path.name.endswith(ext) for ext in file_extensions):
                    continue
                
                # Skip binary files
                if is_binary(file_path):
                    continue
                
                try:
                    # Read file content and check for matches
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        # Search line by line for the pattern
                        for line_num, line in enumerate(file, 1):
                            if search_text in line:
                                # Use relative path for cleaner output
                                rel_path = file_path.relative_to(search_dir)
                                
                                if str(rel_path) not in results:
                                    results[str(rel_path)] = []
                                
                                # Add line context if requested
                                if show_context:
                                    results[str(rel_path)].append((line_num, line.strip()))
                                else:
                                    results[str(rel_path)].append(line_num)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"Error during search: {e}")
    
    return results

def is_binary(file_path):
    """Check if a file is binary to avoid searching binary files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file.read(1024)
            return False
    except UnicodeDecodeError:
        return True

def print_results(results, show_context):
    """Print search results in a readable format"""
    if not results:
        print("\nNo occurrences found.")
        return
    
    print(f"\nFound {sum(len(matches) for matches in results.values())} occurrences in {len(results)} files:")
    print("="*80)
    
    for file_path, matches in sorted(results.items()):
        print(f"\n{file_path} ({len(matches)} occurrences):")
        
        if show_context:
            for line_num, line in matches:
                # Highlight the matched text in the line
                highlighted_line = line.replace('8051', '\033[91m8051\033[0m')
                print(f"  Line {line_num}: {highlighted_line}")
        else:
            line_nums = ', '.join(str(line_num) for line_num in matches)
            print(f"  Lines: {line_nums}")
    
    print("\n" + "="*80)
    print(f"Found {sum(len(matches) for matches in results.values())} occurrences in {len(results)} files.")

def main():
    """Main function to parse arguments and run the search"""
    parser = argparse.ArgumentParser(description='Find port number references in files.')
    parser.add_argument('-d', '--directory', default='.', help='Directory to search in (default: current directory)')
    parser.add_argument('-p', '--port', default='8051', help='Port number to search for (default: 8051)')
    parser.add_argument('-e', '--extensions', default=None, help='Comma-separated list of file extensions to search (default: all common files)')
    parser.add_argument('-c', '--context', action='store_true', help='Show the line containing the match')
    
    args = parser.parse_args()
    
    # Process file extensions
    if args.extensions:
        extensions = [ext.strip() if ext.startswith('.') else f'.{ext.strip()}' for ext in args.extensions.split(',')]
    else:
        extensions = None
    
    # Run the search
    results = find_port_references(args.directory, args.port, extensions, args.context)
    
    # Print results
    print_results(results, args.context)
    
    # Return number of files with matches (for use in scripts)
    return len(results)

if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)