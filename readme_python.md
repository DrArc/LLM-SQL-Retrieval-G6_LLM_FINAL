🏗️ Python IFC Viewer: Full Setup Guide for Cursor IDE
1. Clone Your Project from GitHub
Open Cursor IDE.


Run:


Copy

git clone [your-repo-url]
(Or use Cursor’s built-in Git tools.)

Switch to the correct branch if needed:

Open the Branch menu (lower left), or run:

objective

Copy

git checkout UI3.py
2. Install Project Dependencies
In Cursor’s Terminal (open from the UI or with `Ctrl+``):


Copy

pip install -r requirements.txt
3. Set Up and Activate Your Python/Conda Environment
A. Download & Install Miniconda (if not already installed)

From PowerShell:

powershell
Copy
Edit
wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" -outfile ".\miniconda.exe"
Start-Process -FilePath ".\miniconda.exe" -ArgumentList "/S" -Wait
del .\miniconda.exe


B. Open Anaconda Prompt (not the regular command prompt!)


C. Create and Activate Your Environment:


Copy separate

conda create -n ifcenv python=3.10

conda activate ifcenv


D. Go to Your Project Folder:


replace path amd Copy

cd "path to project"


4. Install Core Geometry & GUI Libraries

Copy and paste

conda install -c conda-forge pythonocc-core
conda install -c conda-forge ifcopenshell
pip install PyQt6 PyQt6-WebEngine PyQt6-WebEngine-Qt6


5. Configure the Python Interpreter in Cursor IDE

Open Command Palette in Cursor (Ctrl+Shift+P).

Type: Python: Select Interpreter

Click or select: [Enter interpreter path]

Find the path to your environment:

In your Anaconda Prompt, run:


Copy

where python

Copy the path for the ifcenv environment (e.g., C:\Users\jlazo\anaconda3\envs\ifcenv\python.exe)

Paste this path into Cursor.

6. (Re-)Activate Your Conda Environment in Cursor Terminal
Every time you start a new terminal or session in Cursor:


Copy

conda activate ifcenv
Keep the Conda Prompt open and active while working and running scripts!

7. Run Your UI Code
Now you can run your app using:


Copy

python scripts/ui3.py

The UI should launch, including the OCC 3D viewer.

Use the “3D File Upload” button to open IFC files and visualize them.


Summary Table


Step	Command / Action
Clone	git clone [repo-url]
Branch	git checkout UI3.py
Install	pip install -r requirements.txt
Conda	conda create -n ifcenv python=3.10
Activate	conda activate ifcenv
Install OCC/IFC	conda install -c conda-forge pythonocc-core ifcopenshell
Install Qt	pip install PyQt6 PyQt6-WebEngine PyQt6-WebEngine-Qt6
Select Interpreter	Use Cursor’s Command Palette and where python
Activate Env	conda activate ifcenv in each terminal
Run UI	python scripts/ui3.py

Tips
Keep your Conda Prompt open as long as you are working.

Always activate the environment in new terminals before running your code.

If you add packages or update requirements, repeat steps in the environment.