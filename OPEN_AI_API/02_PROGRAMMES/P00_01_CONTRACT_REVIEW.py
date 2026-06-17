# Script objective: 
# Use Gemma model to read score contracts for compliance

# - See README.md for set-up instructions

# 1/ Set-up
# 1.1/ Find system paths
import sys as PI_SYS
import os as PI_OS

ZV_BO_IS_KAGGLE = (
    (PI_OS.environ.get('KAGGLE_KERNEL_RUN_TYPE') is not None) or 
    (PI_OS.path.exists('/kaggle/input'))
)
print(f'Using Kaggle: {ZV_BO_IS_KAGGLE}')

if ZV_BO_IS_KAGGLE:
    ZV_ST_KAGGLE_INPUT_FOLDER = PI_OS.path.join(
        PI_OS.sep,
        'kaggle',
        'input'
    )

    ZV_LI_ST_02PROG_FOLDERS = []

    for ZV_ST_CURRENT_FOLDER, ZV_LI_ST_SUBFOLDERS, ZV_LI_ST_FILES in PI_OS.walk(ZV_ST_KAGGLE_INPUT_FOLDER):
        if PI_OS.path.basename(ZV_ST_CURRENT_FOLDER) == '02_PROGRAMMES':
            ZV_LI_ST_02PROG_FOLDERS.append(ZV_ST_CURRENT_FOLDER)

    if not ZV_LI_ST_02PROG_FOLDERS:
        raise FileNotFoundError('No 02_PROGRAMMES folder found under /kaggle/input')

    ZV_ST_02PROG_FOLDER = ZV_LI_ST_02PROG_FOLDERS[0]

    ZV_ST_ROOT_FOLDER = PI_OS.path.dirname(
        ZV_ST_02PROG_FOLDER
    )
else:
    ZV_ST_02PROG_FOLDER = PI_OS.path.dirname(
        PI_OS.path.abspath(__file__)
    )

    ZV_ST_ROOT_FOLDER = PI_OS.path.dirname(
        ZV_ST_02PROG_FOLDER
    )    

PI_SYS.path.append(ZV_ST_02PROG_FOLDER)

# 1.2/ Find and install requirements
from Z_SHARED_FUNCTIONS.FC_INSTALL_REQUIREMENTS import FC_INSTALL_REQUIREMENTS
FC_INSTALL_REQUIREMENTS(ZVFCI_ST_02PROG_FOLDER=ZV_ST_02PROG_FOLDER)

# 1.3/ Find varables and create dictionary
from Z_SHARED_FUNCTIONS.FC_CREATE_DI_VARIABLES import FC_CREATE_DI_VARIABLES
ZV_DI_VARIABLES= FC_CREATE_DI_VARIABLES(ZVFCI_ST_ROOT_FOLDER=ZV_ST_ROOT_FOLDER)

# 1.3/ Import libraries
from huggingface_hub import login as PI_HUGGINGFACE_HUB_LOGIN
import torch as PI_TORCH
import torch._dynamo
from transformers import AutoTokenizer as PI_AUTOTOKENIZER
from transformers import AutoModelForCausalLM as PI_AUTOMODELFORCAUSALLM
import docx as PI_DOCX
from PyPDF2 import PdfReader as PI_PDFREADER
import subprocess as PI_SUBPROCESS
import time as PI_TIME
import re as PI_RE
import pandas as PI_PANDAS
from IPython.display import display as PI_DISPLAY, HTML
import polars as PI_POLARS
import time as PI_TIME

# 1.4/ Import other custom functions
from Z_SHARED_FUNCTIONS.FC_EXPORT import FC_EXPORT_EXCEL_POLARS

# 2/ Variables
ZV_ST_MODEL_ID = ZV_DI_VARIABLES.get('ZV_ST_MODEL_ID')
ZV_ST_HUGGINGFACE_KEY = ZV_DI_VARIABLES.get('ZV_ST_HUGGINGFACE_KEY')
ZV_ST_SOURCES_FOLDER = PI_OS.path.join(
        ZV_ST_ROOT_FOLDER,
        '01_SOURCES'
    )
if ZV_BO_IS_KAGGLE: 
    ZV_ST_RESULTS_FOLDER = PI_OS.path.join(
        PI_OS.sep,
        'kaggle',
        'working'
    )    
else:
    ZV_ST_RESULTS_FOLDER = PI_OS.path.join(
        ZV_ST_ROOT_FOLDER,
        '03_RESULTS'
    )    

        
ZV_BO_TEST_MODE = ((ZV_DI_VARIABLES.get('ZV_ST_TEST_MODE')).lower()=='true')
ZV_LI_CATEGORIES = [
    ZV_ST_CATEGORY.strip()
    for ZV_ST_CATEGORY in ZV_DI_VARIABLES.get('ZV_ST_CATEGORIES').split(',')
]
ZV_BO_TEST_MODE_WO_LLM = ((ZV_DI_VARIABLES.get('ZV_ST_TEST_MODE_WO_LLM')).lower()=='true')
ZV_ST_RESULTS_FILE = ZV_DI_VARIABLES.get('ZV_ST_RESULTS_FILE')

# For testing
# ZV_BO_TEST_MODE = True
# ZV_BO_TEST_MODE_WO_LLM = True

# 3/ Test mode - overwrite variables
if ZV_BO_TEST_MODE:
    ZV_ST_MODEL_ID = 'sshleifer/tiny-gpt2'
    ZV_LI_CATEGORIES = ['Payment terms']
    ZV_NU_MAX_FILES = 1
    ZV_NU_MAX_CHARS = 2000
else:
    ZV_ST_MODEL_ID = ZV_DI_VARIABLES.get('ZV_ST_MODEL_ID')    
    ZV_NU_MAX_FILES = None
    ZV_NU_MAX_CHARS = None

# 3/ Obtain the LLM model objects
print('Start of model download:')
print(f'Model: {ZV_ST_MODEL_ID}')
print(f'Test mode: {ZV_BO_TEST_MODE}')
print(f'LLM disabled: {ZV_BO_TEST_MODE_WO_LLM}')
print(f'Categories: {len(ZV_LI_CATEGORIES)}')

if ZV_BO_TEST_MODE_WO_LLM:
    ZV_OB_TOKENIZER = None
    ZV_OB_LLM_MODEL = None

else:
    # 3.1/ Login to HuggingFace
    PI_HUGGINGFACE_HUB_LOGIN(ZV_ST_HUGGINGFACE_KEY)

    # 3.2/ Create a tokenizer object for the model
    ZV_OB_TOKENIZER = PI_AUTOTOKENIZER.from_pretrained(ZV_ST_MODEL_ID)

    if ZV_OB_TOKENIZER.pad_token is None:
        ZV_OB_TOKENIZER.pad_token = ZV_OB_TOKENIZER.eos_token

    # 3.3/ Create an LLM object for the model (float 16 for reduced memory)
    ZV_OB_LLM_MODEL = PI_AUTOMODELFORCAUSALLM.from_pretrained(
        ZV_ST_MODEL_ID,
        device_map='auto',
        torch_dtype=PI_TORCH.float16
    ) 

    # 3.4/ Disable memory-efficient and flash attention (optional for debugging or compatibility)
    PI_TORCH.backends.cuda.enable_mem_efficient_sdp(True)
    PI_TORCH.backends.cuda.enable_flash_sdp(True)

    # 3.5/ Print which device (CPU/GPU) the model is loaded on
    print(f'Model device: {ZV_OB_LLM_MODEL.device}')

    # 3.6/ Confirm that setup is complete
    print('Run complete')    


# ==========================
# STEP 5: Define File Reading & Text Extraction Functions
# ==========================

# 5.1/ Function: Extract text from DOCX files ---
def FC_EXTRACT_TEXT_FROM_DOCX(ZVFCI_ST_DOCX_PATH):
    ZV_ST_TEXT = ''
    ZV_OB_DOC = PI_DOCX.Document(ZVFCI_ST_DOCX_PATH)
    for ZV_OB_PARAGRAPH in ZV_OB_DOC.paragraphs:
        ZV_ST_TEXT += ZV_OB_PARAGRAPH.text + '\n'
    return ZV_ST_TEXT.strip()

# 5.2/ Function: Extract text from PDF files ---
def FC_EXTRACT_TEXT_FROM_PDF(ZVFCI_ST_PDF_PATH):
    ZV_ST_TEXT = ''
    with open(ZVFCI_ST_PDF_PATH, 'rb') as ZV_OB_FILE:
        ZV_OB_READER = PI_PDFREADER(ZV_OB_FILE)
        for ZV_OB_PAGE in ZV_OB_READER.pages:
            if ZV_OB_PAGE.extract_text():
                ZV_ST_TEXT += ZV_OB_PAGE.extract_text() + '\n'
    return ZV_ST_TEXT.strip()


# 5.3/ Function: Extract text from DOC (97–2003) using antiword ---
def FC_EXTRACT_TEXT_FROM_DOC(ZVFCI_ST_DOC_PATH):
    try:
        ZV_OB_DOC = PI_SUBPROCESS.run(
            [
                'antiword', 
                ZVFCI_ST_DOC_PATH
            ], 
            capture_output=True, 
            text=True
        )
        return ZV_OB_DOC.stdout.strip()
    except Exception as e:
        return f'❌ Error reading DOC file {ZVFCI_ST_DOC_PATH}: {e}'


# ==========================
# STEP 6 : Define response generation function
# ==========================

def FC_GENERATE_RESPONSE(ZVFCI_ST_CONTENT, ZVFCI_LI_CATEGORIES):

    ZV_DI_OUTPUTS = {}
    ZV_TI_START = PI_TIME.time()

    for ZV_ST_CATEGORY in ZVFCI_LI_CATEGORIES:

        ZV_ST_PROMPT = (
            f"Extract only the exact information about '{ZV_ST_CATEGORY}' from the following contract. "
            "Do not explain, summarize, or rephrase. If not found, answer 'None'.\n\nContract:\n"
            + ZVFCI_ST_CONTENT
        )

        ZV_LI_DI_CHAT = [
            {'role': 'user', 'content': ZV_ST_PROMPT}
        ]

        if ZV_OB_TOKENIZER.chat_template is None:
            ZV_ST_CHAT_TEMPLATE = ZV_ST_PROMPT                        
        else:
            ZV_ST_CHAT_TEMPLATE = (
                ZV_OB_TOKENIZER
                .apply_chat_template(
                    ZV_LI_DI_CHAT,
                    tokenize=False,
                    add_generation_prompt=True
                )
            )

        if ZV_BO_TEST_MODE: 
            ZV_LI_LI_INPUT_TOKEN_IDS = (
                ZV_OB_TOKENIZER
                .encode(
                    ZV_ST_CHAT_TEMPLATE,
                    add_special_tokens=False,
                    return_tensors='pt',
                    truncation=True,
                    max_length=512                
                )
                .to(ZV_OB_LLM_MODEL.device)
            )
        else: 
            ZV_LI_LI_INPUT_TOKEN_IDS = (
                ZV_OB_TOKENIZER
                .encode(
                    ZV_ST_CHAT_TEMPLATE,
                    add_special_tokens=False,
                    return_tensors='pt'                
                )
                .to(ZV_OB_LLM_MODEL.device)
            ) 

        if ZV_BO_TEST_MODE:         
            ZV_LI_LI_OUTPUT_TOKEN_IDS = (
                ZV_OB_LLM_MODEL
                .generate(
                    input_ids=ZV_LI_LI_INPUT_TOKEN_IDS,
                    do_sample=True,
                    temperature=0.3,
                    top_p=0.9,
                    max_new_tokens=50,
                    pad_token_id=ZV_OB_TOKENIZER.eos_token_id
                )
            ) 
        else:
            ZV_LI_LI_OUTPUT_TOKEN_IDS = (
                ZV_OB_LLM_MODEL
                .generate(
                    input_ids=ZV_LI_LI_INPUT_TOKEN_IDS,
                    do_sample=True,
                    temperature=0.3,
                    top_p=0.9,
                    max_new_tokens=512
                )
            )           

        ZV_ST_OUTPUT = (
            ZV_OB_TOKENIZER
            .decode(
                ZV_LI_LI_OUTPUT_TOKEN_IDS[0][ZV_LI_LI_INPUT_TOKEN_IDS.shape[-1]:],
                skip_special_tokens=True
            )
            .strip()
        )

        ZV_DI_OUTPUTS[ZV_ST_CATEGORY] = ZV_ST_OUTPUT

    print('✅ Response generated in', round(PI_TIME.time() - ZV_TI_START, 2), 'seconds')

    return ZV_DI_OUTPUTS


# ==========================
# STEP 7 : Clean and organize contract information
# ==========================

def FC_CLEAN_RESPONSE(ZVFCI_DI_OUTPUTS, ZFCI_ST_FILENAME):

    ZV_LI_CATEGORIES = []
    ZV_LI_SENTENCES = []
    
    # Loop through all extracted information
    for ZV_ST_CATEGORY, ZV_ST_STRING in ZVFCI_DI_OUTPUTS.items():
        
        # Split text into sentences
        ZV_LI_ST_SENTENCES = PI_RE.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|:)\s', ZV_ST_STRING)
    
        # Remove irrelevant filler sentences
        ZV_LI_ST_SENTENCES = [
            ZV_ST_SENTENCE for ZV_ST_SENTENCE in ZV_LI_ST_SENTENCES 
            if 'cannot provide'.lower() not in ZV_ST_SENTENCE.lower() and
               'cannot extract'.lower() not in ZV_ST_SENTENCE.lower() and
               'the text does not contain'.lower() not in ZV_ST_SENTENCE.lower() and
               'sure, the information related'.lower() not in ZV_ST_SENTENCE.lower() and
               'sure, here is information'.lower() not in ZV_ST_SENTENCE.lower() and
               'sure, here is the information'.lower() not in ZV_ST_SENTENCE.lower()
        ]
    
        # Join filtered sentences
        ZV_ST_SENTENCES = ' '.join(ZV_LI_ST_SENTENCES)
        if ZV_ST_SENTENCES.strip() == '':
            ZV_ST_SENTENCES = 'None'
    
        # Clean up extra tokens and formatting
        ZV_ST_SENTENCES = ZV_ST_SENTENCES.replace('<eos>', '').replace('\n', ' ').strip()
    
        ZV_LI_CATEGORIES.append(ZV_ST_CATEGORY)
        ZV_LI_SENTENCES.append(ZV_ST_SENTENCES)
    
    # ✅ Create a clean, organized DataFrame
    ZV_DF = PI_PANDAS.DataFrame({
        'ZF_ST_FILENAME': ZFCI_ST_FILENAME,           # <-- Auto-filled real file name
        'ZF_ST_CATEGORY': ZV_LI_CATEGORIES,
        'ZF_ST_SENTENCES': ZV_LI_SENTENCES
    })
    
    # Display the result
    return ZV_DF


# ==========================
# STEP 7 : Read contract files and generate responses
# ==========================

# Initialize an empty list to store all response DataFrames
ZV_LI_DF = []
ZV_LI_ALLOWED_EXTENSIONS = ['docx', 'pdf', 'doc']

# Iterate through each file in the dataset directory
for ZV_NU_FILE_INDEX, ZV_OB_FILE in enumerate(PI_OS.listdir(ZV_ST_SOURCES_FOLDER)):

    ZV_ST_EXTENSION = ZV_OB_FILE.split('.')[-1].lower()

    if ZV_ST_EXTENSION not in ZV_LI_ALLOWED_EXTENSIONS:
        print(f'⚠️ Skipping non-contract file: {ZV_OB_FILE}')
        continue
    
    if ZV_NU_MAX_FILES is not None and len(ZV_LI_DF) >= ZV_NU_MAX_FILES:
        break

    ZV_OB_FILEPATH = PI_OS.path.join(ZV_ST_SOURCES_FOLDER, ZV_OB_FILE)
    ZV_ST_FILENAME = PI_OS.path.basename(ZV_OB_FILE).split('.')[0]

    print(f'Processing file: {ZV_ST_FILENAME}')
    
    # --- Detect file type and extract text accordingly ---
    if ZV_OB_FILEPATH.split('.')[-1] == 'docx':
        print('📘 DOCX file found.')
        ZV_ST_CONTRACT_TEXT = FC_EXTRACT_TEXT_FROM_DOCX(ZV_OB_FILEPATH)
    
    elif ZV_OB_FILEPATH.split('.')[-1] == 'pdf':
        print('📕 PDF file found.')
        ZV_ST_CONTRACT_TEXT = FC_EXTRACT_TEXT_FROM_PDF(ZV_OB_FILEPATH)

    elif ZV_OB_FILEPATH.split('.')[-1] == 'doc':
        print('📗 DOC (97-2003) file found.')
        ZV_ST_CONTRACT_TEXT = FC_EXTRACT_TEXT_FROM_DOC(ZV_OB_FILEPATH)
    
    else:
        print('⚠️ File type not recognized. Skipping this file.')
        continue

    # Test mode
    if ZV_BO_TEST_MODE:
        ZV_ST_CONTRACT_TEXT = ZV_ST_CONTRACT_TEXT[:ZV_NU_MAX_CHARS]

    # --- Step 1: Extraction completed ---
    print('✅ Text extraction complete!')

    # --- Step 2: Generate model response for this contract ---
    print('🧠 Generating model response ...')

    if ZV_BO_TEST_MODE_WO_LLM:
        ZV_DI_RESPONSE = {
            ZV_ST_CATEGORY: 'TEST RESPONSE'
            for ZV_ST_CATEGORY in ZV_LI_CATEGORIES
        }
    else:
        ZV_DI_RESPONSE = FC_GENERATE_RESPONSE(
            ZV_ST_CONTRACT_TEXT,-
            ZV_LI_CATEGORIES
        )
    print('✅ Response generation complete!')        
    # --- Step 3: Clean and structure the model response ---
    print('🧹 Cleaning model response ...')
    ZV_DF_OUTPUTS = FC_CLEAN_RESPONSE(ZV_DI_RESPONSE, ZV_ST_FILENAME)
    print('✅ Response cleaning complete!')
    print('='*50)

    # Append the cleaned response to the main list
    ZV_LI_DF.append(ZV_DF_OUTPUTS)

# ==========================
# STEP 8 : Combine, Format, and Display Final Results
# ==========================

# 🧩 Configure pandas display options
PI_PANDAS.set_option('display.max_rows', 50)           # Limit rows displayed
PI_PANDAS.set_option('display.max_columns', 50)        # Limit columns displayed
PI_PANDAS.set_option('display.max_colwidth', 200)      # Allow wider text before truncating

# 🧠 Combine all response DataFrames into a single table
ZV_DF_ALL_OUTPUTS = PI_PANDAS.concat(ZV_LI_DF, ignore_index=True)

print('✅ All responses combined successfully!')
print(f'Total contracts processed: {len(ZV_LI_DF)}')
print('------------------------------------------------------------')

# 🎨 Create custom CSS for better table visualization
ZV_ST_CUSTOM_CSS = """
<style>
table {
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;  /* Keep columns consistent in width */
    word-wrap: break-word;  /* Allow wrapping within cells */
}
th, td {
    border: 1px solid #ddd;
    text-align: left;       /* Align text to the left */
    padding: 10px;          /* Add spacing for readability */
    vertical-align: top;    /* Align text to top of each cell */
}
th {
    background-color: #f7f7f7;
    font-weight: bold;
}
tr:nth-child(even) {background-color: #fafafa;}
</style>
"""

# 👀 Display scrollable HTML table with clean formatting
print('📋 Formatted full table preview (scroll horizontally if needed):')
ZV_OB_HTML_TABLE = ZV_DF_ALL_OUTPUTS.to_html(index=False, escape=False)
PI_DISPLAY(HTML(ZV_ST_CUSTOM_CSS + f"""
<div style='overflow-x: auto; max-width: 100%; border:1px solid #ddd; padding:12px;'>
{ZV_OB_HTML_TABLE}
</div>
"""))

# 💾 Save to Excel for full offline review
ZV_DF_ALL_OUTPUTS_POLARS = PI_POLARS.from_pandas(ZV_DF_ALL_OUTPUTS)

FC_EXPORT_EXCEL_POLARS(ZV_DF_ALL_OUTPUTS_POLARS,ZV_ST_RESULTS_FOLDER, ZV_ST_RESULTS_FILE)

print(f'✅ Saved formatted results to: {ZV_ST_RESULTS_FOLDER}')
