import os as PI_OS
import polars as PI_POLARS

def FC_EXPORT_EXCEL_POLARS(
        ZVFCI_DF_INPUT,
        ZVFCI_ST_RESULTS_FOLDER,
        ZVFCI_ST_RESULTS_FILE
    ):

    PI_OS.makedirs(
        ZVFCI_ST_RESULTS_FOLDER,
        exist_ok=True
    )

    ZV_ST_FILE_PATH = PI_OS.path.join(
        ZVFCI_ST_RESULTS_FOLDER,
        ZVFCI_ST_RESULTS_FILE
    )

    ZVFCI_DF_INPUT.write_excel(
        ZV_ST_FILE_PATH
    )

    print(
        f'Excel file successfully exported to:\n{ZV_ST_FILE_PATH}'
    ) 