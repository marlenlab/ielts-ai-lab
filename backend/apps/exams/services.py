from .models import Exam, ExamSection


REQUIRED_FULL_MOCK_SECTIONS = (
    ExamSection.SectionType.LISTENING,
    ExamSection.SectionType.READING,
    ExamSection.SectionType.WRITING,
    ExamSection.SectionType.SPEAKING,
)


def are_all_sections_submitted(exam):
    sections = exam.sections.filter(
        section_type__in=REQUIRED_FULL_MOCK_SECTIONS,
    )

    if sections.count() != len(REQUIRED_FULL_MOCK_SECTIONS):
        return False

    return all(
        section.status in (
            ExamSection.Status.SUBMITTED,
            ExamSection.Status.COMPLETED,
        )
        for section in sections
    )


def complete_exam_if_ready(exam):
    if exam.exam_type != Exam.ExamType.FULL_MOCK:
        return False

    if not are_all_sections_submitted(exam):
        return False

    if exam.status != Exam.Status.IN_PROGRESS:
        return False

    from django.utils import timezone

    exam.status = Exam.Status.COMPLETED
    exam.completed_at = timezone.now()

    exam.save(
        update_fields=[
            'status',
            'completed_at',
            'updated_at',
        ],
    )

    return True
