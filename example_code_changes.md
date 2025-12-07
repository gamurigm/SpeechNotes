
## Example Code Changes

This file contains two example pull request patches (in diff format) to demonstrate the recommended approach for improving the codebase.

### 1. Enhance the Testing Suite

This patch adds a new test file to the backend to demonstrate how to add more tests. It creates a `tests` directory in the `src` folder and adds a new test file named `test_main.py` with a simple test.

```diff
diff --git a/src/tests/test_main.py b/src/tests/test_main.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/src/tests/test_main.py
@@ -0,0 +1,8 @@
+import unittest
+
+class TestMain(unittest.TestCase):
+
+    def test_example(self):
+        self.assertEqual(1 + 1, 2)
+
+if __name__ == '__main__':
+    unittest.main()
```

### 2. Improve the Documentation

This patch improves the documentation by adding a section on the deployment process to the `README.md` file. It adds a new section with a detailed guide on how to deploy the application, specifying that the backend and frontend require separate terminal sessions.

```diff
diff --git a/README.md b/README.md
index 3b1f0b1..c1a3b9d 100644
--- a/README.md
+++ b/README.md
@@ -53,6 +53,55 @@

 ---

+## Deployment
+
+This section provides a guide on how to deploy the SpeechNotes application.
+
+### Prerequisites
+
+-   A server with Python 3.10+ and Node.js 18+ installed.
+-   Access to a Riva ASR service.
+-   API keys for NVIDIA and other services.
+
+### Steps
+
+1.  **Clone the repository**:
+    ```bash
+    git clone https://github.com/your-username/speechnotes.git
+    cd speechnotes
+    ```
+
+2.  **Set up the backend**:
+    ```bash
+    cd src
+    pip install -r requirements-agent.txt
+    ```
+
+3.  **Set up the frontend**:
+    ```bash
+    cd web
+    npm install
+    npm run build
+    ```
+
+4.  **Configure the environment variables**:
+    Create a `.env` file in the root directory and add the following environment variables:
+    ```
+    NVIDIA_API_KEY=your-nvidia-api-key
+    RIVA_API_KEY=your-riva-api-key
+    ```
+
+5.  **Start the application**:
+
+    **Note**: The backend and frontend must be run in separate terminal sessions.
+
+    *In one terminal, start the backend:*
+    ```bash
+    cd src
+    python main.py
+    ```
+
+    *In another terminal, start the frontend:*
+    ```bash
+    cd web
+    npm run start
+    ```
+
 ## Comandos útiles
 # SpeechNotes — Descripción del sistema
