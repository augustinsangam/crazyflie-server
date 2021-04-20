from typing import TypedDict, Literal

ProjectType = Literal['cdr', 'rr', 'sandbox']
LogType = Literal['info', 'error', 'success', 'warning']


class LoadProjectData(TypedDict):
    type: ProjectType
    code: str


class LoadProjectLog(TypedDict):
    type: LogType
    log: str
    timestamp: int
