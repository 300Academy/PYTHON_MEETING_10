from pathlib import Path as PI_PATH

def FC_CREATE_DI_VARIABLES(*,ZVFCI_ST_ROOT_FOLDER):

    ZV_OB_ROOT_FOLDER = PI_PATH(ZVFCI_ST_ROOT_FOLDER)

    # 1/ Find .env file
    ZV_LI_OB_PATH_ENV_FILES = list(
        ZV_OB_ROOT_FOLDER.rglob('.env')
    )
    if not ZV_LI_OB_PATH_ENV_FILES:
        raise FileNotFoundError(f'No .env file found under {ZV_OB_ROOT_FOLDER}')

    ZV_OB_PATH_ENV_FILE = ZV_LI_OB_PATH_ENV_FILES[0]

    # 2/ Find AM_VARIABLES.txt
    ZV_LI_OB_PATH_AM_VARIABLE_FILES = list(
        ZV_OB_ROOT_FOLDER.rglob('AM_VARIABLES.txt')
    )
    if not ZV_LI_OB_PATH_AM_VARIABLE_FILES:
        raise FileNotFoundError(f'No AM_VARIABLES.txt file found under {ZV_OB_ROOT_FOLDER}')

    ZV_OB_PATH_AM_VARIABLES_FILE = ZV_LI_OB_PATH_AM_VARIABLE_FILES[0]


    # 6/ Import dotenv module
    from dotenv import dotenv_values as PI_DOTENV_VALUES

    # 7/ Create environment dictionary
    ZV_DI_ENV_VARIABLES = PI_DOTENV_VALUES(ZV_OB_PATH_ENV_FILE)

    # 8/ Create final variables dictionary
    ZV_DI_VARIABLES = PI_DOTENV_VALUES(ZV_OB_PATH_AM_VARIABLES_FILE)
    ZV_DI_VARIABLES.update(ZV_DI_ENV_VARIABLES)

    return ZV_DI_VARIABLES