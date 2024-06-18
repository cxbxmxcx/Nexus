import json

import gradio as gr


def engine_settings_panel():
    engine_options_and_settings = gr.Textbox(
        label="Engine Options and Settings",
        placeholder="{}",
        interactive=False,
        lines=5,
        visible=False,
    )
    with gr.Accordion("Engine Settings", open=False):
        model = gr.Dropdown(
            label="Model",
            choices=[
                "gpt-4o",
                "gpt-4-1106-preview",
                "gpt-3.5-turbo-1106",
                "gpt-4-0613",
                "gpt-4",
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
            ],
            value="gpt-4o",
            interactive=True,
        )
        temperature = gr.Number(
            label="Temperature",
            minimum=0.0,
            maximum=1.0,
            step=0.01,
            value=0.7,
            interactive=True,
        )
        top_p = gr.Number(
            label="Top_p",
            minimum=0.0,
            maximum=1.0,
            step=0.01,
            value=0.9,
            interactive=True,
        )
        max_tokens = gr.Number(
            label="Max Tokens",
            value=256,
            interactive=True,
        )

    engine_settings_cache = {}
    update_engine_settings = False

    def serialize_engine_settings(engine_options_and_settings):
        """Serialize engine options and settings to a JSON string."""
        return json.dumps(engine_options_and_settings, sort_keys=True)

    def update_engine_settings(
        engine_options_and_settings,
    ):
        eos = engine_options_and_settings
        if eos is None or len(eos) < 5:
            return "", 0.7, 0.9, 256
        eos = json.loads(engine_options_and_settings)
        if not isinstance(eos, dict):
            return "", 0.7, 0.9, 256

        engine_options = eos["options"]
        engine_settings = eos["settings"]

        # Serialize the current engine options and settings
        current_engine_settings = serialize_engine_settings(eos)

        # Check if the engine settings are different from the cached settings
        if engine_settings_cache.get("last_settings") == current_engine_settings:
            # Return cached outputs
            return engine_settings_cache["last_output"]

        updated_output = (
            gr.update(
                choices=engine_options.get("model", {}).get("options", []),
                value=engine_settings.get(
                    "model", engine_options.get("model", {}).get("default", "")
                ),
            ),
            gr.update(
                minimum=engine_options.get("temperature", {}).get("min", 0.0),
                maximum=engine_options.get("temperature", {}).get("max", 2.0),
                step=engine_options.get("temperature", {}).get("step", 0.1),
                value=engine_settings.get(
                    "temperature",
                    engine_options.get("temperature", {}).get("default", 0.7),
                ),
            ),
            gr.update(
                minimum=engine_options.get("top_p", {}).get("min", 0.0),
                maximum=engine_options.get("top_p", {}).get("max", 1.0),
                step=engine_options.get("top_p", {}).get("step", 0.1),
                value=engine_settings.get(
                    "top_p", engine_options.get("top_p", {}).get("default", 1.0)
                ),
            ),
            gr.update(
                minimum=engine_options.get("max_tokens", {}).get("min", 100),
                maximum=engine_options.get("max_tokens", {}).get("max", 4096),
                step=engine_options.get("max_tokens", {}).get("step", 10),
                value=engine_settings.get(
                    "max_tokens",
                    engine_options.get("max_tokens", {}).get("default", 1024),
                ),
            ),
        )

        # Update the cache with the current settings and the new output
        engine_settings_cache["last_settings"] = current_engine_settings
        engine_settings_cache["last_output"] = updated_output

        return updated_output

    engine_options_and_settings.change(
        update_engine_settings,
        inputs=[engine_options_and_settings],
        outputs=[model, temperature, top_p, max_tokens],
    )

    def update_settings(
        model, temperature, top_p, max_tokens, engine_options_and_settings
    ):
        eos = engine_options_and_settings

        if eos is None or len(eos) < 5:
            return {"options": {}, "settings": {}}
        eos = json.loads(engine_options_and_settings)
        if not isinstance(eos, dict):
            return {"options": {}, "settings": {}}

        settings = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        eos["settings"] = settings

        # Serialize the current engine options and settings
        current_engine_settings = serialize_engine_settings(settings)

        # Check if the engine settings are different from the cached settings
        # if json.dumps(
        #     engine_settings_cache.get("last_settings"), sort_keys=True
        # ) == json.dumps(current_engine_settings, sort_keys=True):
        #     # Return cached outputs
        #     return engine_options_and_settings
        cache_settings = engine_settings_cache.get("last_engine_settings", "")
        if cache_settings == current_engine_settings:
            # Return cached outputs
            return engine_options_and_settings

        options = eos["options"]
        settings = eos["settings"]

        engine_settings_cache["last_engine_settings"] = serialize_engine_settings(
            settings
        )

        engine_options_and_settings = json.dumps(
            {"options": options, "settings": settings}
        )

        return engine_options_and_settings

    controls = [model, temperature, top_p, max_tokens]

    for control in controls:
        control.change(
            update_settings,
            inputs=controls + [engine_options_and_settings],
            outputs=[engine_options_and_settings],
        )

    return engine_options_and_settings
