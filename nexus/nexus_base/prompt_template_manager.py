class PromptTemplateManager:
    def render_prompt(self, prompt, context):
        for key, value in context.items():
            prompt = prompt.replace("{{$" + key + "}}", value)
        return prompt
