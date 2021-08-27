import shlex


def escape_pipeline_description(desc: str) -> str:
    return ' '.join(shlex.quote(arg) for arg in desc.replace('\n', ' ').split())
