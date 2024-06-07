import contextvars

# This is used to track conversations, or multiple prompt executions in process
tracking_id_context = contextvars.ContextVar("tracking_id")
tracking_function_context = contextvars.ContextVar("tracking_function")
