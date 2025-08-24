#!/usr/bin/env python3
###############################################################################
# Enhanced display functions for search results with aligned output
###############################################################################

import os
from collections import defaultdict
import obt.deco

deco = obt.deco.Deco()

def collect_and_display_results(word_list, path_list, remove_root=None, ext_set=None,
                               case_insensitive=False, regex=False, whole_word=False,
                               invert_match=False, files_only=False,
                               before_context=0, after_context=0,
                               multiple_regex_and=False):
    """
    Collect all results first, then display with perfect alignment and grouped by file.
    """
    from obt.search import search_at_root, search_at_root_multiple_and, ignore_folder_keys, find_multiple_and
    from obt.search_v2 import find_with_context, find_with_context_multiple_and
    from obt.path import Path
    
    # Collect all results grouped by file
    all_results = defaultdict(list)  # filepath -> list of (line_num, line_text, is_match)
    max_path_len = 0
    MAX_FILENAME_LEN = 60  # Maximum filename length
    
    for path in path_list:
        if before_context > 0 or after_context > 0:
            # Context mode - use find_with_context
            for root, dirs, files in os.walk(str(path)):
                for f in files:
                    filepath = os.path.join(root, f)
                    spl = os.path.splitext(filepath)
                    ext = spl[1]
                    
                    # Check if should ignore
                    ignore = False
                    for item in ignore_folder_keys:
                        if item in spl[0]:
                            ignore = True
                            break
                    
                    if ignore or (ext_set and ext not in ext_set):
                        continue
                    
                    # Handle multiple regex AND mode differently
                    if multiple_regex_and and regex:
                        # Process all patterns together with AND logic
                        for context_result in find_with_context_multiple_and(word_list, filepath,
                                                                            case_insensitive, invert_match,
                                                                            before_context, after_context):
                            # Store the filepath for display
                            path_obj = Path(filepath)
                            display_path = path_obj.sanitized
                            if remove_root:
                                r_root = str(remove_root) + "/"
                                display_path = display_path.replace(r_root, "")
                            
                            # Truncate middle if too long
                            if len(display_path) > MAX_FILENAME_LEN:
                                # Keep start and end, truncate middle with "..."
                                keep_start = MAX_FILENAME_LEN // 2 - 2  # -2 for "..."
                                keep_end = MAX_FILENAME_LEN - keep_start - 3  # -3 for "..."
                                display_path = display_path[:keep_start] + "..." + display_path[-keep_end:]
                            
                            # Track max path length
                            max_path_len = max(max_path_len, len(display_path))
                            
                            # Add all lines from this context group
                            for line_num, line_text, is_match in context_result:
                                all_results[display_path].append((line_num, line_text, is_match))
                            
                            # Add separator marker between match groups in same file
                            if all_results[display_path]:
                                all_results[display_path].append((None, None, None))  # Separator
                    else:
                        # Original behavior: process each word separately (OR logic)
                        for word in word_list:
                            for context_result in find_with_context(word, filepath, 
                                                                   case_insensitive, regex, 
                                                                   whole_word, invert_match,
                                                                   before_context, after_context):
                                # Store the filepath for display
                                path_obj = Path(filepath)
                                display_path = path_obj.sanitized
                                if remove_root:
                                    r_root = str(remove_root) + "/"
                                    display_path = display_path.replace(r_root, "")
                                
                                # Truncate middle if too long
                                if len(display_path) > MAX_FILENAME_LEN:
                                    # Keep start and end, truncate middle with "..."
                                    keep_start = MAX_FILENAME_LEN // 2 - 2  # -2 for "..."
                                    keep_end = MAX_FILENAME_LEN - keep_start - 3  # -3 for "..."
                                    display_path = display_path[:keep_start] + "..." + display_path[-keep_end:]
                                
                                # Track max path length
                                max_path_len = max(max_path_len, len(display_path))
                                
                                # Add all lines from this context group
                                for line_num, line_text, is_match in context_result:
                                    all_results[display_path].append((line_num, line_text, is_match))
                                
                                # Add separator marker between match groups in same file
                                if all_results[display_path]:
                                    all_results[display_path].append((None, None, None))  # Separator
        else:
            # Non-context mode
            if multiple_regex_and and regex:
                # Multiple regex patterns with AND logic
                results = search_at_root_multiple_and(word_list, str(path), ext_set=ext_set,
                                                     case_insensitive=case_insensitive,
                                                     invert_match=invert_match,
                                                     files_only=files_only)
                for item in results:
                    path_obj = Path(item.path)
                    display_path = path_obj.sanitized
                    if remove_root:
                        r_root = str(remove_root) + "/"
                        display_path = display_path.replace(r_root, "")
                    
                    # Truncate middle if too long
                    if len(display_path) > MAX_FILENAME_LEN:
                        # Keep start and end, truncate middle with "..."
                        keep_start = MAX_FILENAME_LEN // 2 - 2  # -2 for "..."
                        keep_end = MAX_FILENAME_LEN - keep_start - 3  # -3 for "..."
                        display_path = display_path[:keep_start] + "..." + display_path[-keep_end:]
                    
                    max_path_len = max(max_path_len, len(display_path))
                    
                    if files_only and item.lineno == 0:
                        # Just track the file for files_only mode
                        all_results[display_path] = []
                    else:
                        all_results[display_path].append((item.lineno, item.text, True))
            else:
                # Original behavior: process each word separately (OR logic)
                for word in word_list:
                    results = search_at_root(word, str(path), ext_set=ext_set,
                                            case_insensitive=case_insensitive,
                                            regex=regex, whole_word=whole_word,
                                            invert_match=invert_match,
                                            files_only=files_only)
                    
                    for item in results:
                        path_obj = Path(item.path)
                        display_path = path_obj.sanitized
                        if remove_root:
                            r_root = str(remove_root) + "/"
                            display_path = display_path.replace(r_root, "")
                        
                        # Truncate middle if too long
                        if len(display_path) > MAX_FILENAME_LEN:
                            # Keep start and end, truncate middle with "..."
                            keep_start = MAX_FILENAME_LEN // 2 - 2  # -2 for "..."
                            keep_end = MAX_FILENAME_LEN - keep_start - 3  # -3 for "..."
                            display_path = display_path[:keep_start] + "..." + display_path[-keep_end:]
                        
                        max_path_len = max(max_path_len, len(display_path))
                        
                        if files_only and item.lineno == 0:
                            # Just track the file for files_only mode
                            all_results[display_path] = []
                        else:
                            all_results[display_path].append((item.lineno, item.text, True))
    
    # Now display all results with proper alignment
    if not all_results:
        return
    
    # Print header for each search path
    for idx, search_path in enumerate(path_list):
        if idx == 0 or all_results:  # Only print if we have results
            print("/////////////////////////////////////////////////////////////")
            print("// searching path : %s" % search_path)
            print("/////////")
            break  # Only show first path that has results
    
    # Display each file's results
    first_file = True
    for filepath in sorted(all_results.keys()):
        lines = all_results[filepath]
        
        if files_only and not lines:
            # Files-only mode: just print the filename
            print(deco.path(filepath))
            continue
        
        # Remove trailing None separators
        while lines and lines[-1][0] is None:
            lines.pop()
        
        # Print blank line between files (except first)
        if not first_file:
            print()
        first_file = False
        
        # Display the lines
        # First, find all match lines to determine tree structure
        match_indices = []
        for idx, (line_num, line_text, is_match) in enumerate(lines):
            if line_num is not None and is_match:
                match_indices.append(idx)
        
        first_match_in_file = True
        
        for idx, (line_num, line_text, is_match) in enumerate(lines):
            # Handle separator
            if line_num is None:
                if idx > 0 and idx < len(lines) - 1:  # Don't print separator at start/end
                    # Show vertical line during separators if more matches follow
                    if any(mi > idx for mi in match_indices):
                        path_text = deco.path(" " * (max_path_len - 3) + "│  ")
                        print(deco.formatColumns([(max_path_len + 2, 'right')], [path_text]))
                    else:
                        print()  # Just blank line
                continue
            
            # Determine what to show in the filename column
            if is_match:
                if first_match_in_file:
                    # First match in file: show the full filename
                    path_text = deco.path(filepath)
                    first_match_in_file = False
                else:
                    # Subsequent matches: show tree connector
                    # Check if this is the last match
                    is_last_match = (idx == match_indices[-1])
                    connector = "└──" if is_last_match else "├──"
                    # Position connector properly - vertical line on left, branch extends right
                    path_text = deco.path(" " * (max_path_len - 3) + connector)
            else:
                # Context line - show vertical line if between matches
                if match_indices and idx > match_indices[0] and idx < match_indices[-1]:
                    # We're between first and last match - vertical line on left
                    path_text = deco.path(" " * (max_path_len - 3) + "│  ")
                else:
                    path_text = ""
            
            # Format line number and text
            if is_match:
                line_num_text = deco.yellow(str(line_num))
                content_text = deco.val(line_text.strip())
            else:
                # Context lines
                line_num_text = deco.cyan(str(line_num))
                content_text = deco.inf(line_text.strip())
            
            # Use formatColumns for proper alignment
            # Columns: [filename, line number, content]
            column_configs = [
                (max_path_len + 2, 'right'),  # Filename column, right-aligned
                (8, 'right'),                  # Line number column, right-aligned
                (None, 'left')                 # Content column, no padding
            ]
            column_texts = [path_text, line_num_text, "  " + content_text]
            
            print(deco.formatColumns(column_configs, column_texts))