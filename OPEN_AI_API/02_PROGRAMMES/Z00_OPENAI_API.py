# Script objective:
# Use openAI to give feedback on analytics results

# See README.md for set-up instructions

# 1/ Set-up
# 1.1/ Find programs folder, project root folder

import sys as PI_SYS
import os as PI_OS

ZV_ST_02PROG_FOLDER = PI_OS.path.dirname(
    PI_OS.path.abspath(__file__)
)

ZV_ST_ROOT_FOLDER = PI_OS.path.dirname(
    ZV_ST_02PROG_FOLDER
)   

# 1.2/ Add programs folder to system path
#      (enables import from Z_SHARED_FUNCTIONS)
PI_SYS.path.append(ZV_ST_02PROG_FOLDER)

# 1.3/ Install the requirements
from Z_SHARED_FUNCTIONS.FC_INSTALL_REQUIREMENTS import FC_INSTALL_REQUIREMENTS
FC_INSTALL_REQUIREMENTS(ZVFCI_ST_02PROG_FOLDER=ZV_ST_02PROG_FOLDER)

# 1.4/ Import variables from AM_VARIABLES and .env to a dictionary in RAM
from Z_SHARED_FUNCTIONS.FC_CREATE_DI_VARIABLES import FC_CREATE_DI_VARIABLES
ZV_DI_VARIABLES= FC_CREATE_DI_VARIABLES(ZVFCI_ST_ROOT_FOLDER=ZV_ST_ROOT_FOLDER)

# 1.5/ Import libraries
from openai import OpenAI as PI_OPENAI
import os as PI_OS
import json as PI_JSON
import polars as PI_POLARS
from openai import AuthenticationError as PI_AUHENTICAIONERROR

# 1.6/ Import other custom functions
from Z_SHARED_FUNCTIONS.FC_EXPORT import FC_EXPORT_EXCEL_POLARS

# 2/ Variables
ZV_OPENAI_API_KEY = ZV_DI_VARIABLES.get('ZV_OPENAI_API_KEY')
ZV_ST_SOURCES_FOLDER = PI_OS.path.join(
        ZV_ST_ROOT_FOLDER,
        '01_SOURCES'
    )
ZV_ST_RESULTS_FOLDER = PI_OS.path.join(
        ZV_ST_ROOT_FOLDER,
        '03_RESULTS'
    )

ZV_ST_SOURCE_FILE_NAME=ZV_DI_VARIABLES.get('ZV_ST_SOURCE_FILE_NAME')
ZV_ST_JSON_FILE_NAME=ZV_DI_VARIABLES.get('ZV_ST_JSON_FILE_NAME')
ZV_ST_RESULTS_FILE_NAME = ZV_DI_VARIABLES.get('ZV_ST_RESULTS_FILE_NAME')

# 3/ ChatGPT API function
def Z00_OPENAI_API():

    def FC_CREATE_AI_CLIENT():
        ZV_OB_AI_CLIENT = PI_OPENAI(
            default_headers={"OpenAI-Beta": "assistants=v2"},
            api_key=ZV_OPENAI_API_KEY
        )

        ZV_OB_THREAD = ZV_OB_AI_CLIENT.beta.threads.create()
        ZV_ST_THREAD_ID = ZV_OB_THREAD.id

        return ZV_OB_AI_CLIENT, ZV_ST_THREAD_ID


    def FC_CREATE_AI_ASSISTANT(ZVFCI_AI_CLIENT):
        ZV_ASSISTANT = ZVFCI_AI_CLIENT.beta.assistants.create(
            name="SAP Dashboard Risk Analyst",
            instructions='''
            You are a skilled Data Analyst analyzing SAP dashboards (Order to Cash and others). Your tasks include:
            
            1. **Observations**:
            - Review charts for patterns, anomalies, or inefficiencies.
            
            2. **Risk Assessment**:
            - For each issue, output a Markdown table with:
                - **Issue** (≤10 words)
                - **Priority** (High/Medium/Low)
                - **Observation**
                - **Risk**
                - **Recommendation** (with audit test suggestions)
            
            - Example:
            ```
            | Issue         | Priority | Observation       | Risk                  | Recommendation              |
            |---------------|----------|-------------------|-----------------------|-----------------------------|
            | Excess Billing| High     | Billing > Orders  | Revenue inflation risk| Review periods of variance |
            ```

            3. **Executive Summary**:
            - Summarize all findings clearly for audit teams and senior stakeholders.

            CRITICAL: You MUST include all three sections (### Observations, ### Risk Assessment, ### Executive Summary) in your response.
            Always respond in **Markdown table format**. If formatting fails, retry.
            ''',
            model="gpt-4o-mini",
            tools=[]
        )
        return ZV_ASSISTANT


    def FC_LOAD_TASKS_FROM_JSON(ZVFCI_ST_JSON_FILE_PATH, ZVFCI_ST_JSON_NAME):
        ZV_ST_FILE_PATH = PI_OS.path.join(ZVFCI_ST_JSON_FILE_PATH, ZVFCI_ST_JSON_NAME)
        
        if not PI_OS.path.isfile(ZV_ST_FILE_PATH):
            raise FileNotFoundError(f"Do not find: {ZV_ST_FILE_PATH}")
        
        with open(ZV_ST_FILE_PATH, 'r') as file:
            ZV_DI_ALL_TASKS = PI_JSON.load(file)
        
        return ZV_DI_ALL_TASKS

    def FC_CREATE_AI_PROMPT(
        ZVFCI_ST_DATA_FILE_PATH,
        ZVFCI_ST_DATA_FILE_NAME,
        ZVFCI_DI_TASK
    ):
        ZV_ST_FILE_PATH = PI_OS.path.join(ZVFCI_ST_DATA_FILE_PATH, ZVFCI_ST_DATA_FILE_NAME)
        ZV_DF_DATA = PI_POLARS.read_csv(ZV_ST_FILE_PATH) 
        ZV_DI_DATA = ZV_DF_DATA.to_dict(as_series=False)
        
        ZV_ST_TASK_NAME = ZVFCI_DI_TASK.get('task_name', 'Unknown Task')
        ZV_ST_TASK_TITLE = ZVFCI_DI_TASK.get('task_title', 'Unknown Chart')
        ZV_ST_TASK_CONTENT = ZVFCI_DI_TASK.get('task_content', '')
        
        ZV_ST_PROMPT = (
            f"Analysis Task: {ZV_ST_TASK_NAME}\n"
            f"Chart Title: {ZV_ST_TASK_TITLE}\n\n"
            f"Task Instructions:\n{ZV_ST_TASK_CONTENT}\n\n"
            f"Data:\n{PI_JSON.dumps(ZV_DI_DATA, indent=2)}\n\n"
            f"Please provide your response with:\n"
            f"1. ### Observations section\n"
            f"2. ### Risk Assessment section (as a markdown table)\n"
            f"3. ### Executive Summary section\n"
        )
        
        # print('ZV_ST_PROMPT', ZV_ST_PROMPT)
        
        return ZV_ST_PROMPT, ZV_ST_TASK_TITLE

    def FC_PROCESS_TASK(ZVFCI_AI_CLIENT, ZVFCI_AI_ASSISTANT, ZVFCI_AI_THREAD_ID, ZVFCI_ST_PROMPT):

        # 1/ Add thread, role and content to Client
        ZVFCI_AI_CLIENT.beta.threads.messages.create(
            thread_id=ZVFCI_AI_THREAD_ID,
            role="user",
            content=ZVFCI_ST_PROMPT
        )
            
        # 2/ Try to run AI query
        try:
            ZV_AI_RUN = ZVFCI_AI_CLIENT.beta.threads.runs.create_and_poll(
                thread_id=ZVFCI_AI_THREAD_ID,
                assistant_id=ZVFCI_AI_ASSISTANT.id,
                tools=[]
            )
        
        except PI_AUHENTICAIONERROR as e:
            print("Authentication failed:", str(e))
            
        # 4.3/ Response
        # 4.3.1/ Default - no response
        ZV_ST_RESPONSE_MESSAGE = "No response found."

        # 4.3.2/ Get response if run of AI query successful
        if ZV_AI_RUN:
            ZV_OB_LI_AI_MSG = ZVFCI_AI_CLIENT.beta.threads.messages.list(thread_id=ZVFCI_AI_THREAD_ID, run_id=ZV_AI_RUN.id)
            for ZV_OB_AI_MSG in ZV_OB_LI_AI_MSG.data:
                if ZV_OB_AI_MSG.role == "assistant":
                    content = ZV_OB_AI_MSG.content[0]
                    if hasattr(content, 'text'):
                        ZV_ST_RESPONSE_MESSAGE = content.text.value
                        break
                    elif hasattr(content, 'image'):
                        ZV_ST_RESPONSE_MESSAGE = "[Image Response]"
                        break

        # 5/ Return output
        ZV_DI_AI_RESPONSE ={
            'ZV_ST_RESPONSE_MSG':ZV_ST_RESPONSE_MESSAGE,        
        }
        
        return ZV_DI_AI_RESPONSE
    
    def FC_PARSE_MARKDOWN_TABLE(ZVFCI_ST_TABLE):

        ZV_LI_DI_PARSED_MARKDOWN_ROWS = []

        ZV_LI_ST_LINES = [
            ZV_ST_LINE.strip()
            for ZV_ST_LINE in ZVFCI_ST_TABLE.split('\n')
            if ZV_ST_LINE.strip().startswith('|')
        ]

        for ZV_ST_LINE in ZV_LI_ST_LINES:

            if '---' in ZV_ST_LINE:
                continue

            ZV_LI_ST_VALUES = [
                ZV_ST_VALUE.strip()
                for ZV_ST_VALUE in ZV_ST_LINE.strip('|').split('|')
            ]

            if ZV_LI_ST_VALUES == [
                'Issue',
                'Priority',
                'Observation',
                'Risk',
                'Recommendation'
            ]:
                continue

            if len(ZV_LI_ST_VALUES) == 5:

                ZV_LI_DI_PARSED_MARKDOWN_ROWS.append(
                    {
                        'Issue': ZV_LI_ST_VALUES[0],
                        'Priority': ZV_LI_ST_VALUES[1],
                        'Observation': ZV_LI_ST_VALUES[2],
                        'Risk': ZV_LI_ST_VALUES[3],
                        'Recommendation': ZV_LI_ST_VALUES[4]
                    }
                )

        return ZV_LI_DI_PARSED_MARKDOWN_ROWS  


    def FC_CHATBOT():   
        # 1.1/ Create client and thread ID 
        ZV_OB_AI_CLIENT, ZV_ST_THREAD_ID = FC_CREATE_AI_CLIENT()

        # 1.2/ Create AI assistant
        ZV_AI_ASSISTANT = FC_CREATE_AI_ASSISTANT(ZV_OB_AI_CLIENT)

        # 1.3/ Import JSON tasks
        ZV_DI_ALL_TASKS = FC_LOAD_TASKS_FROM_JSON(ZV_ST_SOURCES_FOLDER, ZV_ST_JSON_FILE_NAME)

        # 1.4/ Loop through all dashboards and tasks
        ZV_LI_DI_RESPONSES = []

        for ZV_ST_DASHBOARD_ID, ZV_LI_DASHBOARD_TASKS in ZV_DI_ALL_TASKS.items():
            for ZV_IN_TASK_INDEX, ZV_DI_TASK in enumerate(ZV_LI_DASHBOARD_TASKS):
                # print(f"\n{'='*80}")
                # print(f"Processing: {ZV_ST_DASHBOARD_ID} - Task {ZV_IN_TASK_INDEX + 1}")
                # print(f"{'='*80}\n")
                
                # Create prompt
                ZV_ST_PROMPT, ZV_ST_CHART_TITLE = FC_CREATE_AI_PROMPT(
                    ZV_ST_SOURCES_FOLDER, 
                    ZV_ST_SOURCE_FILE_NAME, 
                    ZV_DI_TASK
                )

                # Process task
                ZV_DI_AI_RESPONSE = FC_PROCESS_TASK(ZV_OB_AI_CLIENT, ZV_AI_ASSISTANT, ZV_ST_THREAD_ID, ZV_ST_PROMPT)

                # Prepare response
                ZV_DI_JS_RESPONSE = {
                    "dashboard_id": ZV_ST_DASHBOARD_ID,
                    "task_index": ZV_IN_TASK_INDEX + 1,
                    "chart_title": ZV_ST_CHART_TITLE,
                    "response": ZV_DI_AI_RESPONSE['ZV_ST_RESPONSE_MSG'],
                }

                # Separate the table and Executive Summary if applicable
                if "### Executive Summary" in ZV_DI_JS_RESPONSE['response']:
                    ZV_ST_TABLE, ZV_ST_SUMMARY = ZV_DI_JS_RESPONSE['response'].split("### Executive Summary", 1)
                else:
                    ZV_ST_TABLE, ZV_ST_SUMMARY = ZV_DI_JS_RESPONSE['response'], ""

                # Print header with better formatting
                print("\n" + "=" * 80)
                print(f"  {ZV_DI_JS_RESPONSE['chart_title'].upper()}")
                print("=" * 80 + "\n")

                # Print the table content with proper spacing
                ZV_LI_TABLE_LINES = ZV_ST_TABLE.strip().split("\n")
                for ZV_IN_LINE_INDEX, ZV_ST_LINE in enumerate(ZV_LI_TABLE_LINES):
                    # Add extra spacing after headers
                    if ZV_ST_LINE.startswith("###"):
                        if ZV_IN_LINE_INDEX > 0:
                            print()
                        print(ZV_ST_LINE)
                        print("-" * 80)
                    elif ZV_ST_LINE.startswith("|") and "---" in ZV_ST_LINE:
                        # Table separator line
                        print(ZV_ST_LINE)
                    elif ZV_ST_LINE.startswith("|"):
                        # Table content
                        print(ZV_ST_LINE)
                    else:
                        # Regular text
                        print(ZV_ST_LINE)

                # Print executive summary with better formatting
                if ZV_ST_SUMMARY:
                    print("\n" + "-" * 80)
                    print("  EXECUTIVE SUMMARY")
                    print("-" * 80)
                    print(ZV_ST_SUMMARY.strip())

                print("\n" + "=" * 80 + "\n")

                # Parse the markdow information
                ZV_LI_DI_PARSED_MARKDOWN_ROWS = FC_PARSE_MARKDOWN_TABLE(ZV_ST_TABLE)

                # Add to all responses                
                for ZV_DI_PARSED_MARKDOWN_ROW in ZV_LI_DI_PARSED_MARKDOWN_ROWS:

                    ZV_LI_DI_RESPONSES.append(
                        {
                            'dashboard_id': ZV_ST_DASHBOARD_ID,
                            'task_index': ZV_IN_TASK_INDEX + 1,
                            'chart_title': ZV_ST_CHART_TITLE,
                            'Issue': ZV_DI_PARSED_MARKDOWN_ROW['Issue'],
                            'Priority': ZV_DI_PARSED_MARKDOWN_ROW['Priority'],
                            'Observation': ZV_DI_PARSED_MARKDOWN_ROW['Observation'],
                            'Risk': ZV_DI_PARSED_MARKDOWN_ROW['Risk'],
                            'Recommendation': ZV_DI_PARSED_MARKDOWN_ROW['Recommendation'],
                            'Executive Summary': ZV_ST_SUMMARY.strip()
                        }
                    )

        # Return all responses
        return ZV_LI_DI_RESPONSES

  

    ZV_LI_DI_RESPONSES = FC_CHATBOT()
    
    ZV_DF_AI_RESPONSES = PI_POLARS.DataFrame(ZV_LI_DI_RESPONSES)

    FC_EXPORT_EXCEL_POLARS(
        ZV_DF_AI_RESPONSES,
        ZV_ST_RESULTS_FOLDER,
        ZV_ST_RESULTS_FILE_NAME
    )

if __name__ == '__main__':
    Z00_OPENAI_API()
