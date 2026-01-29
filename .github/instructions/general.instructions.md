---
applyTo: '**'
---


rules:
  - Do not create additional Markdown files that duplicate or summarize the project's context or coding guidelines.
  - Only update the root README.md when documentation changes affect the entire project; do not create separate README-like files elsewhere.
  - Read TAREAS.md in the repository root to understand assigned tasks. Mark tasks as completed in that file when finished.
  - During debugging, document your investigation in Debugging_Sessions.md at the project root. This file acts as an index pointing to detailed per-issue debug documents.

debugging:
  instructions:
    - Before starting on a recurring or unresolved problem, check Debugging_Sessions.md to see if the issue has already been investigated.
    - When a problem is resolved, create a detailed file named using the pattern Debugging_[short-description].md.
    - Add an entry in Debugging_Sessions.md referencing the newly created debug document.

tests:
  directory: "tests/"
  naming_pattern: "test_[module_name].py"
  classification:
    unit: Tests that validate isolated functionality of individual modules.
    integration: Tests that validate the interaction between modules or external systems.
  organization: Modules should have corresponding subdirectories under tests/ reflecting their structure, with "unit/" and "integration/" subdivisions when applicable.

documentation:
  readme_language: "Spanish"
  internal_files_language: "English"
