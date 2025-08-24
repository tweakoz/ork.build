#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string, re
import obt.path
import obt.dep
from obt.path import *
import obt.deco
deco = obt.deco.Deco()

#################################################################################

def find_with_context(word, path, case_insensitive=False, regex=False, 
                     whole_word=False, invert_match=False,
                     before_context=0, after_context=0):
    """
    Find matches with optional context lines.
    Yields tuples of (line_number, line_text, is_match, context_lines)
    """
    # Prepare the search pattern
    if regex:
        if case_insensitive:
            pattern = re.compile(word, re.IGNORECASE)
        else:
            pattern = re.compile(word)
    elif whole_word:
        word_pattern = r'\b' + re.escape(word) + r'\b'
        if case_insensitive:
            pattern = re.compile(word_pattern, re.IGNORECASE)
        else:
            pattern = re.compile(word_pattern)
    elif case_insensitive:
        word_lower = word.lower()
        pattern = None
    else:
        pattern = None
    
    if not os.path.exists(str(path)):
        return
    
    try:
        with open(path, "rb") as fp:
            lines = []
            for line in fp:
                try:
                    lines.append(line.decode("utf-8").rstrip("\n"))
                except:
                    lines.append("")  # Placeholder for non-decodable lines
            
            matches = []
            for n, line in enumerate(lines):
                matched = False
                
                if pattern:  # Regex or whole-word search
                    matched = bool(pattern.search(line))
                elif case_insensitive:  # Case-insensitive substring
                    matched = word_lower in line.lower()
                else:  # Simple substring
                    matched = word in line
                
                # Apply invert-match if requested
                if invert_match:
                    matched = not matched
                
                if matched:
                    matches.append(n)
            
            # Now yield results with context
            for match_idx in matches:
                context_result = []
                
                # Before context
                for i in range(max(0, match_idx - before_context), match_idx):
                    context_result.append((i + 1, lines[i], False))
                
                # The match itself
                context_result.append((match_idx + 1, lines[match_idx], True))
                
                # After context
                for i in range(match_idx + 1, min(len(lines), match_idx + after_context + 1)):
                    context_result.append((i + 1, lines[i], False))
                
                yield context_result
    except Exception:
        pass

#################################################################################

def find_with_context_multiple_and(patterns, path, case_insensitive=False, 
                                  invert_match=False,
                                  before_context=0, after_context=0):
    """
    Find matches where ALL patterns match (AND logic), with optional context lines.
    Used when multiple -r options are provided.
    """
    # Compile all patterns
    compiled_patterns = []
    for pattern_str in patterns:
        if case_insensitive:
            compiled_patterns.append(re.compile(pattern_str, re.IGNORECASE))
        else:
            compiled_patterns.append(re.compile(pattern_str))
    
    if not os.path.exists(str(path)):
        return
    
    try:
        with open(path, "rb") as fp:
            lines = []
            for line in fp:
                try:
                    lines.append(line.decode("utf-8"))
                except:
                    lines.append("")  # Handle decode errors gracefully
            
            # Find all matches
            match_indices = []
            for i, line in enumerate(lines):
                # Check if ALL patterns match
                all_matched = True
                for pattern in compiled_patterns:
                    if not pattern.search(line):
                        all_matched = False
                        break
                
                # Apply invert-match if requested
                if invert_match:
                    all_matched = not all_matched
                
                if all_matched:
                    match_indices.append(i)
            
            # Group matches with their context
            if match_indices:
                processed = set()
                for match_idx in match_indices:
                    if match_idx in processed:
                        continue
                    
                    # Determine context range
                    start = max(0, match_idx - before_context)
                    end = min(len(lines), match_idx + after_context + 1)
                    
                    # Mark all lines in this context group as processed
                    for i in range(start, end):
                        processed.add(i)
                    
                    # Yield the context group
                    context_group = []
                    for i in range(start, end):
                        line_num = i + 1
                        line_text = lines[i]
                        is_match = (i == match_idx)
                        context_group.append((line_num, line_text, is_match))
                    
                    yield context_group
    except Exception:
        pass

#################################################################################

def execute_at_v2(word_list, path_list, remove_root=None, ext_set=None,
                 case_insensitive=False, regex=False, whole_word=False,
                 invert_match=False, files_only=False,
                 before_context=0, after_context=0):
    """
    Enhanced execute_at with all new options.
    """
    if ext_set is None:
        ext_set = set(os.environ.get("OBT_SEARCH_EXTLIST", ".cpp:.c:.h:.py:.txt").split(":"))
    
    ignore_folder_keys = set(["/obj/", "/pluginobj/", "/.build/"])
    
    for path in path_list:
        print("/////////////////////////////////////////////////////////////")
        print("// searching path : %s" % path)
        print("/////////")
        
        for word in word_list:
            found_files = set()
            
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
                    
                    if ignore or ext not in ext_set:
                        continue
                    
                    if files_only:
                        # Just check if file has matches
                        for _ in find_with_context(word, filepath, case_insensitive, 
                                                  regex, whole_word, invert_match, 0, 0):
                            found_files.add(filepath)
                            break
                    else:
                        # Display with optional context
                        has_context = before_context > 0 or after_context > 0
                        match_count = 0
                        
                        for context_result in find_with_context(word, filepath, 
                                                               case_insensitive, regex, 
                                                               whole_word, invert_match,
                                                               before_context, after_context):
                            match_count += 1
                            
                            # Print delimiter before match group if using context
                            if has_context and match_count > 1:
                                print()  # Blank line delimiter between match groups
                            
                            for line_num, line_text, is_match in context_result:
                                pathstr = str(filepath)
                                if remove_root:
                                    r_root = str(remove_root) + "/"
                                    pathstr = pathstr.replace(r_root, "")
                                
                                deco_path = "%-*s" % (72, deco.path(pathstr))
                                
                                if is_match:
                                    # Highlight matching lines
                                    deco_lino = "%s %s" % (deco.magenta("Line"), deco.yellow(line_num))
                                    deco_lino = "%-*s" % (37, deco_lino)
                                    deco_text = deco.val(line_text.strip())
                                else:
                                    # Context lines in dimmer color
                                    deco_lino = "%s %s" % (deco.bright("    "), deco.bright(str(line_num)))
                                    deco_lino = "%-*s" % (37, deco_lino)
                                    deco_text = deco.bright(line_text.strip())
                                
                                print("%s%s %s" % (deco_path, deco_lino, deco_text))
            
            # Handle files_only mode
            if files_only and found_files:
                for filepath in sorted(found_files):
                    pathstr = str(filepath)
                    if remove_root:
                        r_root = str(remove_root) + "/"
                        pathstr = pathstr.replace(r_root, "")
                    print(deco.path(pathstr))

#################################################################################

# Keep backward compatibility exports
def execute_at(word_list, path_list, remove_root=None, ext_set=None):
    """
    Backward compatible version without new options.
    """
    execute_at_v2(word_list, path_list, remove_root, ext_set)