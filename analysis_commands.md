# Static and Dynamic Analysis Commands

This document provides a list of static and dynamic analysis commands and scripts that can be used to reproduce the findings of this audit locally on Windows with VS Code.

## 1. Static Analysis

Static analysis is the process of analyzing code without executing it. It can be used to identify a wide range of issues, such as security vulnerabilities, performance bottlenecks, and coding style violations.

### Backend (Python)

The following static analysis tools can be used for the Python backend:

-   **`pylint`**: A popular linter for Python that checks for errors, enforces a coding standard, and looks for code smells.
    ```bash
    pip install pylint
    pylint src/
    ```
-   **`bandit`**: A tool for finding common security issues in Python code.
    ```bash
    pip install bandit
    bandit -r src/
    ```
-   **`mypy`**: A static type checker for Python that can help to identify type errors in the code.
    ```bash
    pip install mypy
    mypy src/
    ```

### Frontend (Next.js)

The following static analysis tools can be used for the Next.js frontend:

-   **`eslint`**: A popular linter for JavaScript and TypeScript that checks for errors and enforces a coding standard.
    ```bash
    cd web
    npm install eslint
    npm run lint
    ```
-   **`prettier`**: A code formatter that can be used to automatically format the code according to a consistent style.
    ```bash
    cd web
    npm install prettier
    npx prettier --write .
    ```

## 2. Dynamic Analysis

Dynamic analysis is the process of analyzing code while it is executing. It can be used to identify a wide range of issues, such as memory leaks, performance bottlenecks, and security vulnerabilities.

### Backend (Python)

The following dynamic analysis tools can be used for the Python backend:

-   **`cProfile`**: A built-in profiler for Python that can be used to identify performance bottlenecks in the code.
    ```bash
    python -m cProfile -o profile.pstats src/main.py
    ```
-   **`memory-profiler`**: A tool for monitoring the memory usage of a Python program.
    ```bash
    pip install memory-profiler
    python -m memory_profiler src/main.py
    ```

### Frontend (Next.js)

The following dynamic analysis tools can be used for the Next.js frontend:

-   **Lighthouse**: An open-source, automated tool for improving the quality of web pages. It can be run in Chrome DevTools or as a command-line tool.
-   **Next.js Analytics**: A built-in analytics tool for Next.js that can be used to monitor the performance of the application.

## 3. VS Code Integration

The following VS Code extensions can be used to integrate the static and dynamic analysis tools into the development workflow:

-   **Python**: The official Python extension for VS Code, which provides support for linting, debugging, and testing.
-   **ESLint**: An extension for integrating ESLint into VS Code.
-   **Prettier**: An extension for integrating Prettier into VS Code.
