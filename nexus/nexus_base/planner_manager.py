import importlib
import json
import os
import re

from nexus.nexus_base.global_values import GlobalValues


class Plan:
    def __init__(self, prompt: str, goal: str, plan_text: str):
        self.prompt = prompt
        self.goal = goal
        self._generated_plan = self._extract_json(plan_text)
        # self.generated_plan = json.loads(self.plan_json)

    def __str__(self):
        return f"Prompt: {self.prompt}\nGoal: {self.goal}\nPlan: {self._generated_plan}"

    def __repr__(self):
        return str(self)

    @property
    def generated_plan(self):
        return self._generated_plan

    @generated_plan.setter
    def generated_plan(self, value):
        self._generated_plan = value

    def _extract_json(self, text):
        # Try to find JSON enclosed in backticks
        backtick_pattern = r"```(?:\w*\n)?(.*?)```"
        match = re.search(backtick_pattern, text, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
        else:
            # If not in backticks, find JSON between curly braces
            brace_pattern = r"\{.*\}"
            match = re.search(brace_pattern, text, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No JSON found in the text")

        # Parse the JSON
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def _extract_json_from_text(self, text):
        # Extract the JSON block using a regular expression
        json_block_match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if not json_block_match:
            try:
                json_block = json.loads(text)
                json_block = json.dumps(json_block)
            except Exception as e:
                print(f"Error decoding JSON: {e}")
                raise ValueError("No JSON block found in the text")
        else:
            json_block = json_block_match.group(1).strip()

        # Parse the JSON block
        try:
            parsed_json = json.loads(json_block)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        return parsed_json


class NexusPlanner:
    def __init__(self):
        self.name = self.__class__.__name__

    def create_plan(self, nexus, agent, goal: str, prompt: str) -> Plan:
        """This function should be implemented in the subclass."""
        raise NotImplementedError

    def execute_plan(self, nexus, agent, plan: Plan) -> str:
        """This function should be implemented in the subclass."""
        raise NotImplementedError


class PlannerManager:
    def __init__(self):
        planners_folder = os.path.join(
            os.path.dirname(__file__), GlobalValues.PLANNERS_FOLDER
        )
        self.planners = self._load_planners(planners_folder)

    def get_planner(self, planner_name):
        for planner in self.planners:
            if planner.name == planner_name:
                return planner
        raise ValueError(f"Planner {planner_name} not found")

    def get_planners(self):
        return self.planners

    def get_planner_names(self):
        return [planner.name for planner in self.planners]

    def _load_planners(self, planners_folder):
        planners = []
        for filename in os.listdir(planners_folder):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    module_name = filename[:-3]
                    module_path = os.path.join(planners_folder, filename)
                    spec = importlib.util.spec_from_file_location(
                        module_name, module_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if (
                            isinstance(attribute, type)
                            and issubclass(attribute, NexusPlanner)
                            and attribute is not NexusPlanner
                        ):
                            planners.append(attribute())
                except Exception as e:
                    print(f"Error loading planner from {filename}: {e}")
        return planners
