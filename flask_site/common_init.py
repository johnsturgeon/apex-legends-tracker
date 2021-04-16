"""
call settings = get_settings(),this will load the settings
"""
import os
import json
import shutil


def get_settings():
    """
    Get the settings for the current environment

    Return:
        returns a dictionary of settings.
    """
    settings_file = config_filepath() + '/settings.json'

    # if there is no user settings file, then we should copy the template file
    # to create the settings file
    if not os.path.isfile(settings_file):
        shutil.copyfile(config_filepath() + '../config/settings_template.json', settings_file)
    with open(settings_file) as config_file:
        app_settings = json.load(config_file)
    return app_settings


def set_settings(new_settings: dict):
    """
    Set the settings for the current environment
    NOTE:
        This will overwrite any previous settings

    """
    with open(config_filepath() + '/settings.json', 'w') as config_file:
        json.dump(new_settings, config_file, indent=4)


def config_filepath() -> str:
    """
    returns the normalized filepath for the config file.
    """
    relative_conf_json = './'
    dirname = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(dirname, relative_conf_json))
