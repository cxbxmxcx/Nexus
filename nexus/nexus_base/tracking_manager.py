import time

from nexus.nexus_base.context_variables import (
    tracking_function_context,
    tracking_id_context,
)
from nexus.nexus_base.nexus_models import (
    AgentEngineUsage,
    db,
)


class TrackingManager:
    def __init__(self):
        pass

    def get_next_id(self):
        return int(time.time())

    @staticmethod
    def track_agent_engine_usage(
        id=None,
        name="Agent",
        model="gpt-3.5-turbo",
        in_tokens=0,
        out_tokens=0,
        elapsed_time=0,
    ):
        with db.atomic():
            tracking_id = tracking_id_context.get("Not Set")
            tracking_function = tracking_function_context.get("Not Set")
            if AgentEngineUsage.select().where(AgentEngineUsage.id == id).exists():
                raise ValueError("Response ID already exists")
            AgentEngineUsage.create(
                id=id,
                tracking_id=tracking_id,
                function=tracking_function,
                name=name,
                model=model,
                in_tokens=in_tokens,
                out_tokens=out_tokens,
                elapsed_time=elapsed_time,
            )

    def track_chat_create(self, original_create, agent_name):
        def wrapper(self, *args, **kwargs):
            start = time.time()
            result = original_create(*args, **kwargs)
            end = time.time()

            TrackingManager.track_agent_engine_usage(
                id=result.id,
                name=agent_name,
                model=result.model,
                in_tokens=result.usage.prompt_tokens,
                out_tokens=result.usage.completion_tokens,
                elapsed_time=int(end - start),
            )
            return result

        return wrapper

    def track_messages_create(self, original_create, agent_name):
        def wrapper(self, *args, **kwargs):
            start = time.time()
            model = ""
            id = ""
            in_tokens = 0
            out_tokens = 0
            stream = original_create(*args, **kwargs)

            def wrap_stream(stream):
                try:
                    for item in stream:
                        if item.__class__.__name__ == "MessageStartEvent":
                            model = item.message.model
                            id = item.message.id
                            in_tokens = item.message.usage.input_tokens
                        elif item.__class__.__name__ == "MessageDeltaEvent":
                            out_tokens = item.usage.output_tokens
                        yield item  # Yield the items as they come from the original stream

                except GeneratorExit:
                    print(f"{agent_name}: Stream was closed by the consumer.")
                    raise
                except Exception as e:
                    print(f"{agent_name}: Error in stream: {e}")
                    raise
                finally:
                    end = time.time()
                    TrackingManager.track_agent_engine_usage(
                        id=id,
                        name=agent_name,
                        model=model,
                        in_tokens=in_tokens,
                        out_tokens=out_tokens,
                        elapsed_time=int(end - start),
                    )

            if stream.__class__.__name__ == "Stream":
                return wrap_stream(stream)
            elif stream.__class__.__name__ == "Message":
                end = time.time()
                TrackingManager.track_agent_engine_usage(
                    id=stream.id,
                    name=agent_name,
                    model=stream.model,
                    in_tokens=stream.usage.input_tokens,
                    out_tokens=stream.usage.output_tokens,
                    elapsed_time=int(end - start),
                )
                return stream

        return wrapper

    def get_tracking_usage(self):
        return AgentEngineUsage.select().dicts()
