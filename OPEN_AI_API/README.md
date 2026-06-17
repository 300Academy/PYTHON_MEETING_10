# 300Framework – 300F_OPENAI_API
---
---
Send results table to openAI and get in return a tabe with Observation|Risk|Recommendation|Priority from a pre-trained assistant.

## Instructions
This program does not require you to input the root folder address. The program will infer the folder address. However, you need to make sure that you respect the folder structure as mentioned below for this inference to work.

### 1/ Create Virtual Environment 

For this project, we need to use the 3.14 version of Python, because this is compatible with PI_SUBPROCESS, that we use to automatically install the Python libraries. 

Ensure that you have Python version 3.14 on your machine. If you do not have it, download it from https://www.python.org/downloads. 

In Visual Studio Code, open a PowerShell terminal (View-> Terminal) at the location: (you can use cd - change directory - to navigate to the 02_PROGRAMMES folder)

```text
PS C...\02_PROGRAMMES
```
Ensure that the address in the terminal matches C:\YourProjectRootFolder\02_PROGRAMMES.
The rest of the instructions are commands that we will run in the Powershell terminal at this location.

```bash
py -3.14 -m venv venv
```
After running, check that you have a \venv folder created inside 02_PROGRAMMES and that it contains python.exe inside \venv\Scripts and that you see pip3.14.exe

---

### 2/ Activate Virtual Environment using the Powershell activation program

```powershell
.\venv\Scripts\Activate.ps1
```
After activation, open a Python File from the 02_PROGRAMMES folder and check that the virtual environment, mentioned in the bottom-right corner of VSC, points to the python.exe inside your \venv\Scripts folder. If it does not, click on the venv mentioned in the bottom-right of VSC and browse to choose the correct python.exe from the \venv\Scripts folder.

---

### 3/ Install the required libraries, using the requirements.txt file. 

In this python project, the requirements will be installed automatically based on requirements.txt

### 4/ Create a .env file from the .env.example 

Updat the .env.example to your own Kaggle key. Then rename it as .env. See the webclass presentation for how to create an openAI key.

```bash
ZV_ST_OPENAI_API_KEY=sk-XXXXXXXXXXXXXXX-k8EA
```

### 5/ Run the script

Set the variables in AM_VARIABLES as follows (already set for you - but you can update if you want to try with different files):

If test mode is successful run with: 
```text
ZV_ST_SOURCE_FILE_NAME=01_RESULTS_DATASET.csv
ZV_ST_JSON_FILE_NAME=AI_INSTRUCTIONS.json
ZV_ST_RESULTS_FILE_NAME=01_AI_RESPONSE.xlsx
```

Once the variables set, type the following in the terminal of VSC or press Run Python file. 

```bash
python 300F_OPENAI_API.py
```

If your VSC is picking up the wrong python.exe - ensure that your venv folder is in the 02_PROGRAMMES folder and that the terminal is in the 02_PROGRAMMES folder and then run the script with direct reference to the python.exe in the virtual environment: 

```bash
.\venv\Scripts\python.exe 300F_OPENAI_API.py
```

---
---

## Overview

This Python project sends an example data analytics result to openAI and exports a table with columns: **Issue|Priority|Observation|Risk|	Recommendation***

The objective of the test is to automatically generate recommendations for audit fieldwork testing and to support understanding of the test results.

## Known required improvements

- None at the moment

## Typically used by

This test is commonly used by:

- Internal auditors
- Internal controllers
- Treasury department

This test is used to highlight contracts that are not compliant with internal control guidelines.

---

## Project Structure

```text
ROOT_FOLDER/
│
├── 01_SOURCES/
│   ├── 01_RESULTS_DATASET.csv
│   ├── AI_INSTRUCTIONS.json
│   └── AM_VARIABLES.txt
│
├── 02_PROGRAMMES/
│   ├── 300F_OPENAI_API.py
│   ├── .env.example: update and change to .env
│   ├── pyproject.toml
│   └── requirements.txt
│
```

# SAP Source Files

```text
The analysis does not work on SAP data. This analysis is based on an example results data set.

```

---

## Variables

The names of the dataset and JSON instruction files can be updated in:

```text
01_SOURCES/AM_VARIABLES.txt
```

## General best-practice reminders

- Results should be reviewed and interesting samples taken: simple NLP models may only be 90% accurate, especially if the small model is used.
- Results should be reviewed by qualified audit or procurement professionals and samples discussed with the business before any action plans or audit recommendations are drafted.

---

## 300Framework

300Framework provides AI-enhanced data audit analytics, for SAP environments, helping audit teams compute risk indicators, identify control weaknesses and sample high-risk transactions and third-parties.












