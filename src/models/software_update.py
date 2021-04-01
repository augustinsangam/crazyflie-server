from typing import TypedDict, Literal

ProjectType = Literal['cdr', 'rr', 'sandbox']


class LoadProjectData(TypedDict):
    type: ProjectType
    code: str
