from nexus.nexus_base.action_manager import agent_action
from nexus.nexus_base.environment_manager import EnvironmentManager


@agent_action
def run_python_code(code, filename=None):
    """Runs the given code in a virtual environment."""
    env_manager = EnvironmentManager()
    code_output, code_errors = env_manager.run_code(code, filename=filename)
    return code_output, code_errors


@agent_action
def get_latest_code():
    """Returns the latest working Python code that was last run in the virtual environment."""
    env_manager = EnvironmentManager()
    latest_code = env_manager.get_latest_code()
    return latest_code


@agent_action
def run_shell_command(command):
    """Runs the given shell command in a virtual environment."""
    env_manager = EnvironmentManager()
    shell_output, shell_errors = env_manager.run_shell_command(command)
    return shell_output, shell_errors


@agent_action
def install_package(package):
    """Installs the given package in a virtual environment."""
    env_manager = EnvironmentManager()
    env_manager.install_package(package)
    return f"Installed package: {package}"
