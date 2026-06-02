================================================================================
                         VIRALSCANNER (C++ VERSION) - USER GUIDE
================================================================================

HOW TO USE THE BUTTONS & CONTROLS

This guide explains what each button does and how to use ViralScanner to scan
and analyze C++ code for security vulnerabilities.

================================================================================
THE MAIN INTERFACE LAYOUT
================================================================================

The ViralScanner window is divided into 4 areas:

1. CENTER: Code Editor
   - Where you view and edit C++ code
   
2. LEFT SIDE: Project Workspace (Folder Tree)
   - Shows your project files and folders
   
3. BOTTOM: Scan Output (Results Window)
   - Shows scan results and security warnings
   
4. RIGHT SIDE: Control Panel (Buttons)
   - All the buttons to control the app

================================================================================
BUTTON GUIDE
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ BUTTON 1: "OPEN FILE"                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ WHAT IT DOES:                                                               │
│   Opens a file browser dialog so you can select a C++ file to scan.         │
│                                                                              │
│ HOW TO USE:                                                                 │
│   1. Click the "OPEN FILE" button                                          │
│   2. A file browser window will appear                                      │
│   3. Navigate to your C++ file (.cpp, .h, .hpp, etc.)                      │
│   4. Select the file and click "Open"                                       │
│   5. The file will appear in the code editor                               │
│   6. The folder tree on the left will show all files in that folder        │
│                                                                              │
│ RESULT:                                                                     │
│   - File content appears in the code editor                                │
│   - Folder tree is populated with all project files                        │
│   - Ready to scan the file for security issues                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ BUTTON 2: "SCAN FILE"                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ WHAT IT DOES:                                                               │
│   Analyzes the C++ code in the editor for security vulnerabilities.        │
│                                                                              │
│ HOW TO USE:                                                                 │
│   1. Make sure you have C++ code in the editor (use "OPEN FILE" first)     │
│   2. Click the "SCAN FILE" button                                          │
│   3. The scan runs in the background (app stays responsive)                │
│   4. Results appear in the "Scan Output" window at the bottom              │
│                                                                              │
│ WHAT TO LOOK FOR:                                                          │
│   • RED TEXT = Security warnings (risky includes, unsafe functions)        │
│   • Line numbers = Exactly where the problem is in your code              │
│   • BLACK TEXT = Status messages ("Scanning started...", etc.)             │
│                                                                              │
│ RESULT:                                                                     │
│   - Dangerous C++ functions are identified (strcpy, gets, scanf, etc.)     │
│   - Risky includes are flagged (system.h, socket.h, unistd.h, etc.)       │
│   - Exact line numbers are shown for each finding                          │
│   - "Scan complete." message appears when done                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ BUTTON 3: "TOGGLE THEME"                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ WHAT IT DOES:                                                               │
│   Switches between Light Theme and Dark Theme for the interface.           │
│                                                                              │
│ HOW TO USE:                                                                 │
│   1. Click the "TOGGLE THEME" button                                       │
│   2. The entire interface changes colors                                    │
│   3. Click again to switch back                                            │
│                                                                              │
│ LIGHT THEME:                                                                │
│   - White background                                                        │
│   - Black text                                                              │
│   - Default when app starts                                                 │
│   - Good for bright environments                                            │
│                                                                              │
│ DARK THEME:                                                                 │
│   - Dark gray/black background (#1e1e1e)                                   │
│   - Light gray text                                                         │
│   - Reduces eye strain in dark rooms                                        │
│   - Better for night coding sessions                                        │
│                                                                              │
│ RESULT:                                                                     │
│   - Interface colors invert                                                 │
│   - Code editor colors change                                              │
│   - All buttons and windows update                                          │
│   - Your preference is not saved (resets on restart)                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ BUTTON 4: "RELOAD PLUGINS"                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ WHAT IT DOES:                                                               │
│   Reloads all custom plugin security checks from the plugins folder.       │
│                                                                              │
│ HOW TO USE:                                                                 │
│   1. Create custom scan plugins in the plugins folder (advanced)           │
│   2. Each plugin must have a scan() function                               │
│   3. Click "RELOAD PLUGINS" to load them                                   │
│   4. Results appear in the Scan Output window                              │
│                                                                              │
│ WHAT HAPPENS:                                                              │
│   - The app searches the plugins folder for .py files                      │
│   - Each plugin file is loaded and tested                                  │
│   - Shows how many plugins were loaded                                     │
│   - Shows any plugin errors if they failed to load                         │
│                                                                              │
│ RESULT:                                                                     │
│   - Custom security checks are now active                                  │
│   - Next time you scan, plugins will be included                           │
│   - Plugin errors are shown in red in the output                           │
│   - Message shows: "Loaded X plugin(s)."                                   │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
PROJECT WORKSPACE (LEFT SIDE - FOLDER TREE)
================================================================================

WHAT IT IS:
   A tree view showing all files and folders in your project directory.

HOW TO USE IT:
   1. After opening a file, the workspace tree populates automatically
   2. Folders are shown with expand/collapse arrows
   3. Click the arrow to expand a folder and see its contents
   4. Double-click any file to open it in the code editor
   5. Hidden files (starting with .) are automatically ignored

NAVIGATING FILES:
   • Folders show first, then files (sorted alphabetically)
   • Double-click a C++ file to view it
   • The editor updates instantly
   • You can open and scan multiple files without clicking "OPEN FILE" again

================================================================================
SCAN OUTPUT WINDOW (BOTTOM - RESULTS)
================================================================================

WHAT IT SHOWS:
   • Status messages (Scanning started... / Scan complete.)
   • Security vulnerabilities found (RED TEXT = risky code)
   • Line numbers where each problem is located
   • Plugin errors (if any plugins fail)

HOW TO READ IT:
   Example:
   ┌─────────────────────────────────────────────────────────┐
   │ Scan Output                                              │
   │ Scanning started...                                      │
   │ Risky include at line 3: socket.h                       │ ← RED
   │ Unsafe call at line 15: strcpy()                        │ ← RED
   │ Unsafe call at line 22: gets()                          │ ← RED
   │ Scan complete.                                           │
   └─────────────────────────────────────────────────────────┘

WHAT RED TEXT MEANS:
   • "Risky include:" = You're using a dangerous library
   • "Unsafe call:" = You're using a dangerous function
   • These can cause security vulnerabilities

WHAT BLACK TEXT MEANS:
   • Status messages
   • Scan progress
   • Plugin information

================================================================================
FILE MENU (TOP)
================================================================================

HOW TO USE:
   1. Click "File" at the top of the window
   2. Click "Open" to open a file
   3. This does the same thing as the "OPEN FILE" button

================================================================================
TYPICAL WORKFLOW
================================================================================

STEP 1: Open a C++ File
   → Click "OPEN FILE" button
   → Select your .cpp or .h file
   → File appears in editor

STEP 2: Scan the File
   → Click "SCAN FILE" button
   → Watch results appear in output window
   → Red warnings show security issues

STEP 3: Review Results
   → Look at line numbers in output
   → Find and review the dangerous code in the editor
   → Fix the security issues in your code

STEP 4: Rescan
   → After making fixes, click "SCAN FILE" again
   → If warnings are gone, your code is safer

STEP 5: Browse Other Files (Optional)
   → Double-click other files in the workspace tree
   → Repeat steps 2-4 for each file

================================================================================
TIPS & TRICKS
================================================================================

✓ USE KEYBOARD SHORTCUTS:
  • Ctrl+O = Open File (same as "OPEN FILE" button)
  
✓ COMMON SECURITY WARNINGS:
  • strcpy() → Use strncpy() or secure copy functions
  • gets() → Use fgets() instead
  • scanf() → Use secure input validation
  • fork() / exec() → Be careful with process creation
  • system() → Avoid if possible, validate all inputs
  
✓ DARK THEME:
  • Great for late night coding sessions
  • Reduces eye strain
  • Click "TOGGLE THEME" to switch instantly
  
✓ MULTIPLE FILES:
  • Use the workspace tree to quickly switch between files
  • No need to click "OPEN FILE" each time
  • Just double-click in the tree to jump to another file

✓ PLUGIN DEVELOPMENT:
  • Advanced users can create custom security checks
  • Place .py files in the plugins folder
  • Must include a scan(code) function
  • Click "RELOAD PLUGINS" to test your plugin

================================================================================
NEED HELP?
================================================================================

If ViralScanner shows no issues:
   → Your C++ code passed the basic security checks
   → It may still have other vulnerabilities not detected
   → Always code defensively and validate all inputs

If ViralScanner crashes:
   → Make sure you have Python 3.8+ installed
   → Make sure PyQt6 is installed
   → Close the app and restart it
   → Try opening a simple C++ file first

If plugins don't load:
   → Check that plugin files end in .py
   → Check that each plugin has a scan(code) function
   → Check for syntax errors in your plugin code
   → Click "RELOAD PLUGINS" after fixing

================================================================================
