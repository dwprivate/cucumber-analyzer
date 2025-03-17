from typing import List, Optional, Literal
from pydantic import BaseModel, Field, RootModel


class Location(BaseModel):
    line: int
    column: int


class LocationTag(BaseModel):
    name: str
    type: str
    location: Location


class Tag(BaseModel):
    name: str



class Argument(BaseModel):
    val: Optional[str] = None
    offset: Optional[int] = None


class Match(BaseModel):
    location: Optional[str] = None
    arguments: Optional[List[Argument]] = None


StatusType = Literal["passed", "failed", "skipped", "undefined", "pending"]


class Result(BaseModel):
    status: StatusType
    duration: Optional[int] = None
    error_message: Optional[str] = None


class Hook(BaseModel):
    match: Match
    result: Result


class DocString(BaseModel):
    line: int
    value: str
    content_type: Optional[str] = None


class DataTableRow(BaseModel):
    cells: List[str]


class Step(BaseModel):
    keyword: str
    line: int
    name: str
    result: Result
    match: Optional[Match] = None
    doc_string: Optional[DocString] = None
    rows: Optional[List[DataTableRow]] = None


class Element(BaseModel):
    line: int
    type: Literal["background", "scenario"]
    keyword: str
    name: str
    description: str
    steps: List[Step]
    start_timestamp: Optional[str] = None
    id: Optional[str] = None
    before: Optional[List[Hook]] = None
    after: Optional[List[Hook]] = None
    tags: Optional[List[Tag]] = None


class Feature(BaseModel):
    uri: str
    id: str
    line: int
    keyword: str
    name: str
    description: str
    elements: List[Element]
    tags: Optional[List[LocationTag]] = None


class CucumberReport(RootModel):
    root: List[Feature]



# == Non Standard
class ElementSummary(BaseModel):
    # line: int
    type: Literal["background", "scenario"]
    # keyword: str
    name: str
    description: str
    # steps: List[Step]

    start_timestamp: Optional[str] = None
    id: Optional[str] = None
    # before: Optional[List[Hook]] = None
    # after: Optional[List[Hook]] = None
    tags: Optional[List[str]] = None    
    result: Result
    failing_step: Step | None   

class FeatureSummary(Feature):
    # uri: str
    # id: str
    # line: int
    # keyword: str
    # name: str
    # description: str
    elements: List[ElementSummary]
    tags: Optional[List[LocationTag]] = None
# == Transformers

class CucumberReportSummary(RootModel):
    root: List[FeatureSummary]

def summarize_element(element: Element) -> ElementSummary:
    failing_step =  next((step for step in element.steps if step.result.status != "passed"), None)
    return ElementSummary(
        type = element.type,
        name = element.name,
        description = element.description,
        start_timestamp = element.start_timestamp,
        id = element.id,
        tags = [tag.name for tag in element.tags] if element.tags else [],
        failing_step = failing_step,
        result = Result(
            status = failing_step.result.status if failing_step else "passed", 
            duration = sum(s.result.duration for s in element.steps),
             error_message = None
             )
    )    
def summarize_feature(feature: Feature, only_errors=False) -> FeatureSummary:
    summary = FeatureSummary(
        uri = feature.uri,
        id = feature.id,
        line = feature.line,
        keyword = feature.keyword,
        name = feature.name,
        description=feature.description,
        tags = feature.tags,
        elements=[summarize_element(e) for e in feature.elements]
    )
    if only_errors:
        print(len(summary.elements))
        summary.elements = [e for e in summary.elements if e.failing_step is not None]
        print(len(summary.elements))        
    return summary

def summarize_cucumber_report(report: CucumberReport, only_errors=False) -> CucumberReportSummary:
    summary = CucumberReportSummary([summarize_feature(f, only_errors) for f in report.root])
    if only_errors:
        summary.root = [f for f in summary.root if f.elements]
    return summary
