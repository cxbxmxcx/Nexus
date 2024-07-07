import os

from nexus.nexus_base.action_manager import agent_action
from nexus.nexus_base.global_values import GlobalValues


@agent_action
def create_project(project_name):
    """
    Create a project. Projects are collection of files and folders.
    :param project_name: The name of the project.
    """
    # Check if the folder exists, return unsuccessful if it exists
    if os.path.exists(project_name):
        return f"Project '{project_name}' already exists."

    # Create a folder with the project name
    folder_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, project_name)
    os.makedirs(folder_path)

    return f"Project '{project_name}' created successfully."


@agent_action
def add_file_to_project(project_name, filename, content):
    """
    Add a file to a project.
    :param project_name: The name of the project.
    :param filename: The name of the file including extension.
    :param content: The content to save in the file.
    """
    # Check if the project exists, return unsuccessful if it does not exist
    if not os.path.exists(project_name):
        return f"Project '{project_name}' does not exist."

    # Check if the file exists, return unsuccessful if it exists
    file_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, project_name, filename)
    if os.path.exists(file_path):
        return f"File '{filename}' already exists in project '{project_name}'."

    # Save content to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(content))

    return f"File '{filename}' added to project '{project_name}' successfully."


@agent_action
def remove_file_from_project(project_name, filename):
    """
    Remove a file from a project.
    :param project_name: The name of the project.
    :param filename: The name of the file including extension.
    """
    # Check if the project exists, return unsuccessful if it does not exist
    if not os.path.exists(project_name):
        return f"Project '{project_name}' does not exist."

    # Check if the file exists, return unsuccessful if it does not exist
    file_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, project_name, filename)
    if not os.path.exists(file_path):
        return f"File '{filename}' does not exist in project '{project_name}'."

    # Delete the file
    os.remove(file_path)

    return f"File '{filename}' removed from project '{project_name}' successfully."


@agent_action
def get_project_files(project_name):
    """
    Get a list of files in a project.
    :param project_name: The name of the project.
    :return: A list of files in the project.
    """
    # Check if the project exists, return unsuccessful if it does not exist
    if not os.path.exists(project_name):
        return f"Project '{project_name}' does not exist."

    # Get the list of files in the project
    project_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, project_name)
    files = os.listdir(project_path)

    return files


@agent_action
def get_project_file_contents(project_name, filename):
    """
    Get the contents of a file in a project.
    :param project_name: The name of the project.
    :param filename: The name of the file including extension.
    :return: The content of the file.
    """
    # Check if the project exists, return unsuccessful if it does not exist
    if not os.path.exists(project_name):
        return f"Project '{project_name}' does not exist."

    # Check if the file exists, return unsuccessful if it does not exist
    file_path = os.path.join(
        GlobalValues.ASSISTANTS_WORKING_FOLDER, project_name, filename
    )
    if not os.path.exists(file_path):
        return f"File '{filename}' does not exist in project '{project_name}'."

    # Load content from the file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return content
