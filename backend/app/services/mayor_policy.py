from dataclasses import dataclass
from decimal import Decimal

from backend.app.models import CityDistrict

APPROVED = "approved"
REVISION_REQUIRED = "revision_required"


@dataclass(frozen=True)
class BuildingProposal:
    project_type: str
    land_area_hectares: Decimal
    expected_jobs: int = 0
    traffic_load: int = 0
    service_load: int = 0
    medical_load: int = 0
    public_benefit: int = 0
    owner_city_land_share_pct: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class MayorPolicyIssue:
    code: str
    message: str


@dataclass(frozen=True)
class MayorPolicyDecision:
    status: str
    score: int
    summary: str
    issues: tuple[MayorPolicyIssue, ...]
    questions: tuple[str, ...]


PROJECT_ZONE_RULES: dict[str, set[str]] = {
    "residential": {"residential", "suburban", "expansion"},
    "commercial": {"commercial", "transit", "residential", "suburban", "expansion"},
    "industrial": {"industrial", "expansion"},
    "civic": {
        "transit",
        "commercial",
        "residential",
        "industrial",
        "suburban",
        "expansion",
    },
    "medical": {
        "transit",
        "commercial",
        "residential",
        "industrial",
        "suburban",
        "expansion",
    },
}


def evaluate_building_proposal(
    district: CityDistrict, proposal: BuildingProposal
) -> MayorPolicyDecision:
    issues: list[MayorPolicyIssue] = []
    questions: list[str] = []

    project_type = proposal.project_type.strip().lower()
    allowed_zones = PROJECT_ZONE_RULES.get(project_type)
    if allowed_zones is None:
        _add_issue(
            issues,
            questions,
            "unknown_project_type",
            "AI-мер не розпізнає тип забудови.",
            "Уточніть тип проєкту: residential, commercial, industrial, civic або medical.",
        )
    elif district.zone_type not in allowed_zones:
        _add_issue(
            issues,
            questions,
            "zoning_mismatch",
            f"Тип забудови '{project_type}' не відповідає зоні району '{district.zone_type}'.",
            "Поясніть, чому цей проєкт має бути саме в цьому районі, або змініть район/тип забудови.",
        )

    if proposal.land_area_hectares <= Decimal("0.00"):
        _add_issue(
            issues,
            questions,
            "invalid_land_area",
            "Площа землі має бути більшою за нуль.",
            "Вкажіть реальну площу ділянки в гектарах.",
        )
    elif proposal.land_area_hectares > Decimal(str(district.land_available_hectares)):
        _add_issue(
            issues,
            questions,
            "land_capacity",
            "Запитана площа більша за доступний резерв району.",
            "Зменшіть площу або оберіть район із більшим земельним резервом.",
        )

    if proposal.owner_city_land_share_pct >= Decimal("35.00") and project_type not in {
        "civic",
        "medical",
    }:
        _add_issue(
            issues,
            questions,
            "anti_monopoly_review",
            "Заявник уже контролює значну частку землі міста.",
            "Поясніть суспільну користь проєкту або запропонуйте партнерську/відкриту модель володіння.",
        )

    if project_type == "industrial" and district.desirability >= 65:
        _add_issue(
            issues,
            questions,
            "residential_comfort_risk",
            "Промисловий проєкт у бажаному для життя районі може знизити якість середовища.",
            "Додайте план шумозахисту, екології та відокремлення від житлових зон.",
        )

    if project_type in {"residential", "commercial"} and district.crime_risk >= 40:
        _add_issue(
            issues,
            questions,
            "security_plan_required",
            "Район має підвищений ризик злочинності.",
            "Додайте план безпеки: освітлення, охорона, маршрути до поліції або приватна безпека.",
        )

    if district.traffic + proposal.traffic_load > 85:
        _add_issue(
            issues,
            questions,
            "traffic_plan_required",
            "Проєкт перевантажить транспорт району.",
            "Покажіть план під'їздів, паркування або громадського транспорту.",
        )

    if district.service_coverage - proposal.service_load < 30:
        _add_issue(
            issues,
            questions,
            "service_capacity_required",
            "Базові сервіси району можуть не витримати навантаження.",
            "Додайте компенсацію: комунальні роботи, сервісний внесок або нижче навантаження.",
        )

    if (
        project_type in {"residential", "commercial"}
        and district.medical_coverage - proposal.medical_load < 30
    ):
        _add_issue(
            issues,
            questions,
            "medical_access_required",
            "Медичне покриття району недостатнє для такого навантаження.",
            "Додайте доступ до медицини: медпункт, страхове покриття або договір із клінікою.",
        )

    if project_type == "commercial" and proposal.expected_jobs <= 0:
        _add_issue(
            issues,
            questions,
            "jobs_plan_required",
            "Комерційний проєкт має пояснити вплив на робочі місця.",
            "Вкажіть очікувану кількість вакансій і вимоги до працівників.",
        )

    score = _score_decision(issues)
    status = APPROVED if not issues else REVISION_REQUIRED
    summary = (
        "AI-мер погоджує заявку для наступного етапу."
        if status == APPROVED
        else "AI-мер повертає заявку на доопрацювання."
    )

    return MayorPolicyDecision(
        status=status,
        score=score,
        summary=summary,
        issues=tuple(issues),
        questions=tuple(questions),
    )


def _add_issue(
    issues: list[MayorPolicyIssue],
    questions: list[str],
    code: str,
    message: str,
    question: str,
) -> None:
    issues.append(MayorPolicyIssue(code=code, message=message))
    questions.append(question)


def _score_decision(issues: list[MayorPolicyIssue]) -> int:
    penalty_by_code = {
        "unknown_project_type": 35,
        "zoning_mismatch": 30,
        "invalid_land_area": 35,
        "land_capacity": 25,
        "anti_monopoly_review": 25,
        "residential_comfort_risk": 20,
        "security_plan_required": 15,
        "traffic_plan_required": 15,
        "service_capacity_required": 15,
        "medical_access_required": 15,
        "jobs_plan_required": 10,
    }
    score = 100 - sum(penalty_by_code.get(issue.code, 10) for issue in issues)
    return max(0, score)
