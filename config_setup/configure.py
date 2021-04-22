""" Setup script
Run after checkout to set the project up, read the project README for more details
"""
import shutil
import sys
import os
from distutils.sysconfig import get_python_lib
from rich.prompt import Prompt
from rich.console import Console

sys.path.append('flask_site')
# pylint: disable=C0413
# pylint: disable=E0401
import common_init  # noqa C0413 E0401


def main():
    """ Run after checkout to set the project up, read the project README for more details """
    console = Console(width=80)
    console.print("\n\n[bold dark yellow]Welcome!\n\n", justify="center")
    message = """This file will set up the apex legends tracker.
[blue]NOTE:[/blue] You can re-run this to change any of the configuration settings.\n\n"""
    console.print(message)
    console.print("0. making the conf folder")
    if not os.path.isdir("conf"):
        os.mkdir('conf')
    # Copy the `additional_paths.pth` file to the site-packages folder
    console.print("1. [italic pale_green3]Moving paths file into site packages -->")
    source_file_path = common_init.config_filepath() + '/../config_setup/additional_paths.pth'
    shutil.copyfile(source_file_path, get_python_lib() + '/additional_paths.pth')
    console.print("[b green]Done!\n")

    # get settings if they exist
    console.print(
        "2. [italic pale_green3]Getting current settings (or default settings if no previous"
    )
    settings = common_init.get_settings()
    console.print("[b green]Done!\n", highlight=True)
    console.print(
        '3. [italic pale_green3]Enter any new settings[/italic pale_green3]'
        '[magenta](default in parenthesis)\n'
    )
    for key in settings:
        description = settings[key].get('description')
        default_value = None if not settings[key].get('value') else settings[key].get('value')
        is_password = False
        if 'password' in key:
            is_password = True
        choices = None if not settings[key].get('choices') else settings[key].get('choices')
        try:
            new_value = Prompt.ask(
                f"Enter the [red]{description}[/red]",
                default=default_value,
                show_default=(not is_password),
                choices=choices,
                password=is_password
            )
        except KeyboardInterrupt:
            console.print("\n\n[red]Exiting[/red] without saving!\n")
            sys.exit(0)
        if settings[key]['value'] != new_value:
            console.print(f"[green]Updating setting [/green]{key}")
        settings[key]['value'] = new_value

    # save settings dict to settings.json
    console.print("\n4. Saving the settings file ...")
    common_init.set_settings(settings)
    console.print("\n\n[green]SUCCESS!\n\n")


if __name__ == "__main__":
    main()
