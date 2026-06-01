from pydantic import BaseModel


class VacancyItem(BaseModel):
    id: str
    business_name: str
    title: str
    salary_per_hour: float
    min_education: str
    energy_cost: int


class VacanciesData(BaseModel):
    vacancies: list[VacancyItem]


class ExamQuestionData(BaseModel):
    id: int
    text: str
    options: list[str]


class ExamInfoData(BaseModel):
    exam_id: str
    title: str
    cost_to_take: float
    passing_score: int
    time_limit_seconds: int
    description: str
    questions: list[ExamQuestionData]
