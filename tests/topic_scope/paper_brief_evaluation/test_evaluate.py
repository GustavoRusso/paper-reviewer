"""evaluate_paper_brief: skip, no-op, happy path, parse failure, force re-judge."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper_brief import get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    PaperBriefEvaluation,
)
from paper_reviewer.topic_scope.paper_brief_evaluation import evaluate_paper_brief
from tests.topic_scope.generate_paper_brief.helpers import (
    add_brief,
    create_test_paper,
    sample_brief_content,
)
from tests.topic_scope.paper_brief_evaluation.helpers import (
    add_succeeded_brief,
    sample_evaluation,
    set_evaluation,
)

_LICENSE_STUB = (
    "Abstract\n\n"
    "Orthoflaviviruses depend on host metabolic resources.\n\n"
    "Full Text Availability\n\n"
    "The license terms selected by the author(s) for this preprint "
    "version do not permit archiving in PMC. The full text is "
    "available from the preprint server.\n"
)


def test_missing_paper_fails_without_creating_brief(
    session_factory: sessionmaker[Session],
) -> None:
    calls: list[str] = []

    result = evaluate_paper_brief(
        9_999_999,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.paper_id == 9_999_999
    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "Paper id 9999999 not found"
    assert calls == []

    session = session_factory()
    try:
        assert get_paper_brief_by_paper_id(session, 9_999_999) is None
    finally:
        session.close()


def test_missing_brief_does_not_call_judge_or_create_row(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    calls: list[str] = []

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.status is PaperAspectStatus.not_started
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        assert get_paper_brief_by_paper_id(session, paper_id) is None
    finally:
        session.close()


def test_skips_judge_when_brief_is_not_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.failed,
        error_message="prior brief failure",
    )
    calls: list[str] = []

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.status is PaperAspectStatus.not_started
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.failed
        assert brief.evaluation_status is PaperAspectStatus.not_started
        assert brief.evaluation is None
        assert brief.evaluation_score is None
    finally:
        session.close()


def test_noop_when_evaluation_succeeded_and_force_false(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    original = sample_evaluation()
    add_succeeded_brief(
        session_factory,
        paper_id,
        content=sample_brief_content(summary="Already done."),
    )
    set_evaluation(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        evaluation=original,
        evaluation_score=Decimal("4.25"),
    )
    calls: list[str] = []

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation is not None
        assert brief.evaluation["faithfulness"]["score"] == 5
        assert brief.evaluation_score == Decimal("4.25")
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.content is not None
        assert brief.content["summary"] == "Already done."
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_noop_when_evaluation_failed_and_force_false(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_succeeded_brief(session_factory, paper_id)
    set_evaluation(
        session_factory,
        paper_id,
        status=PaperAspectStatus.failed,
        evaluation_error_message="prior judge failure",
    )
    calls: list[str] = []

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "prior judge failure"
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation_status is PaperAspectStatus.failed
        assert brief.evaluation_error_message == "prior judge failure"
        assert brief.evaluation is None
        assert brief.evaluation_score is None
        assert brief.status is PaperAspectStatus.succeeded
    finally:
        session.close()


def test_unusable_full_text_fails_evaluation_without_judge(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        full_text_status=PaperAspectStatus.succeeded,
        full_text_plain=_LICENSE_STUB,
    )
    add_succeeded_brief(
        session_factory,
        paper_id,
        content=sample_brief_content(summary="Keep this brief."),
    )
    calls: list[str] = []

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: calls.append("judge")
        or sample_evaluation(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "full_text_plain is not usable article body"
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation_status is PaperAspectStatus.failed
        assert brief.evaluation is None
        assert brief.evaluation_score is None
        assert brief.evaluation_error_message == (
            "full_text_plain is not usable article body"
        )
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.content is not None
        assert brief.content["summary"] == "Keep this brief."
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_happy_path_persists_evaluation_and_mean_score(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        full_text_plain="UNIQUE_FULL_TEXT_BODY",
    )
    content = sample_brief_content(summary="Grounded takeaway.")
    add_succeeded_brief(session_factory, paper_id, content=content)
    seen: dict[str, object] = {}

    def judge(
        full_text_plain: str,
        *,
        content: PaperBriefContent,
    ) -> PaperBriefEvaluation:
        seen["full_text"] = full_text_plain
        seen["summary"] = content.summary
        return sample_evaluation()

    result = evaluate_paper_brief(
        paper_id,
        session_factory=session_factory,
        judge_evaluation=judge,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert seen["full_text"] == "UNIQUE_FULL_TEXT_BODY"
    assert seen["summary"] == "Grounded takeaway."

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation_status is PaperAspectStatus.succeeded
        assert brief.evaluation_error_message is None
        assert brief.evaluation is not None
        assert set(brief.evaluation) == {
            "faithfulness",
            "completeness",
            "conciseness",
            "topic_agnostic",
        }
        assert "evaluation_score" not in brief.evaluation
        assert brief.evaluation["faithfulness"]["score"] == 5
        assert brief.evaluation["completeness"]["score"] == 4
        assert brief.evaluation_score == Decimal("4.25")
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.content is not None
        assert brief.content["summary"] == "Grounded takeaway."
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_parse_failure_fails_evaluation_and_keeps_brief(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_succeeded_brief(
        session_factory,
        paper_id,
        content=sample_brief_content(summary="Keep this brief."),
    )
    set_evaluation(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        evaluation=sample_evaluation(),
        evaluation_score=Decimal("4.25"),
    )

    def judge(
        full_text_plain: str,
        *,
        content: PaperBriefContent,
    ) -> PaperBriefEvaluation:
        raise ValueError("LLM returned no JSON object\n\nAssistant output:\nnot-json")

    result = evaluate_paper_brief(
        paper_id,
        force=True,
        session_factory=session_factory,
        judge_evaluation=judge,
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message is not None
    assert "Assistant output:" in result.error_message
    assert "not-json" in result.error_message

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation_status is PaperAspectStatus.failed
        assert brief.evaluation is None
        assert brief.evaluation_score is None
        assert brief.evaluation_error_message is not None
        assert "Assistant output:" in brief.evaluation_error_message
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.content is not None
        assert brief.content["summary"] == "Keep this brief."
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_force_true_rejudges_succeeded_evaluation(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_succeeded_brief(
        session_factory,
        paper_id,
        content=sample_brief_content(summary="Keep this brief."),
    )
    set_evaluation(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        evaluation=sample_evaluation(),
        evaluation_score=Decimal("4.25"),
    )

    result = evaluate_paper_brief(
        paper_id,
        force=True,
        session_factory=session_factory,
        judge_evaluation=lambda *_a, **_k: sample_evaluation(
            faithfulness=sample_evaluation().faithfulness.model_copy(
                update={"score": 3}
            ),
            completeness=sample_evaluation().completeness.model_copy(
                update={"score": 3}
            ),
            conciseness=sample_evaluation().conciseness.model_copy(update={"score": 3}),
            topic_agnostic=sample_evaluation().topic_agnostic.model_copy(
                update={"score": 3}
            ),
        ),
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.evaluation is not None
        assert brief.evaluation["faithfulness"]["score"] == 3
        assert brief.evaluation_score == Decimal("3.00")
        assert brief.evaluation_status is PaperAspectStatus.succeeded
        assert brief.evaluation_error_message is None
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.content is not None
        assert brief.content["summary"] == "Keep this brief."
    finally:
        session.close()
