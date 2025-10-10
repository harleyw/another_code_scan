import getpass
import os


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("OPENAI_API_KEY")
# _set_env("COHERE_API_KEY")
# _set_env("TAVILY_API_KEY")
_set_env("DASHSCOPE_API_KEY")
