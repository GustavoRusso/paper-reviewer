"""Enqueue create_topic_brief with zero-briefed and in-flight guards."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_scope.topic_brief import (
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    CreateTopicBriefEnqueueResult,
)
from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    count_briefed_references,
)


def enqueue_create_topic_brief(
    session: Session,
    topic_scope_id: int,
    *,
    submit: Callable[[int], None],
) -> CreateTopicBriefEnqueueResult:
    """Reset or create TopicBrief, then submit create_topic_brief when allowed.

    Commits the in-flight ``not_started`` row before submit so durable UI
    polling can see it even if Prefect starts immediately.
    """
    if count_briefed_references(session, topic_scope_id) == 0:
        return CreateTopicBriefEnqueueResult(skipped_no_briefed=True)

    brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
    if brief is not None and brief.status is PaperAspectStatus.not_started:
        return CreateTopicBriefEnqueueResult(skipped_in_flight=True)

    if brief is None:
        brief = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
    brief.status = PaperAspectStatus.not_started
    brief.error_message = None
    session.commit()
    submit(topic_scope_id)
    return CreateTopicBriefEnqueueResult(submitted=True)
