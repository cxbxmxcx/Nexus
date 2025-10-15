import os
import yaml


class AgentProfile:
    def __init__(
        self,
        name,
        avatar,
        persona,
        actions,
        knowledge,
        memory,
        evaluators,
        reasoners,
        planners,
        feedback,
        orchestration=None,  # ⭐ ADDED orchestration parameter to __init__
    ):
        self.name = name
        self.avatar = avatar
        self.persona = persona
        self.actions = actions
        self.knowledge = knowledge
        self.memory = memory
        # ⭐ FIXED: Changed from evalutors to evaluators (corrected typo)
        self.evaluators = evaluators  # Fixed original typo for compatibility
        self.reasoners = reasoners
        self.planners = planners
        self.feedback = feedback
        self.orchestration = orchestration  # ⭐ ADDED store orchestration in instance


class ProfileManager:
    def __init__(self):
        self.directory = os.path.join(os.path.dirname(__file__), "nexus_profiles")
        self.agent_profiles = []
        self.load_profiles()

    def load_profiles(self):
        # Scan the directory for YAML files
        for filename in os.listdir(self.directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.directory, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    profile_data = yaml.safe_load(file)
                    self.create_agent_profile(profile_data)

    def create_agent_profile(self, profile_data):
        if "agentProfile" in profile_data:
            profile = profile_data["agentProfile"]
            agent = AgentProfile(
                name=profile.get("name", ""),
                avatar=profile.get("avatar", ""),
                persona=profile.get("persona", ""),
                actions=profile.get("actions", []),
                knowledge=profile.get("knowledge", None),
                memory=profile.get("memory", None),
                evaluators=profile.get("evaluators", None),
                reasoners=profile.get("reasoners", None),
                planners=profile.get("planners", None),
                feedback=profile.get("feedback", None),
                orchestration=profile.get("orchestration", None),  # ⭐ ADDED orchestration to profile creation
            )
            self.agent_profiles.append(agent)

    def get_agent_profile(self, profile_name):
        for profile in self.agent_profiles:
            if profile.name == profile_name:
                return profile
        return None

    def get_agent_profile_names(self):
        return [profile.name for profile in self.agent_profiles]

    # ⭐ NEW METHOD: Get only orchestrator profiles (those with orchestration config)
    def get_orchestrator_profile_names(self):
        """Get only orchestrator profiles (those with orchestration config)."""
        return [
            profile.name 
            for profile in self.agent_profiles 
            if profile.orchestration is not None
        ]

    # ⭐ NEW METHOD: Check if a profile is an orchestrator profile
    def is_orchestrator_profile(self, profile_name):
        """Check if a profile is an orchestrator profile."""
        profile = self.get_agent_profile(profile_name)
        return profile is not None and profile.orchestration is not None

