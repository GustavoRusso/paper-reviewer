"""Prefect flow: create a TopicBrief for one Topic scope."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    CreateTopicBriefResult,
)
from paper_reviewer.topic_scope.topic_brief_generation.create import (
    create_topic_brief as _create_topic_brief,
)


@flow(name="create_topic_brief")
def create_topic_brief(
    topic_scope_id: int,
    force: bool = True,
) -> CreateTopicBriefResult:
    """Prefect entrypoint: draft or rewrite one TopicBrief.

    The Topic brief generation page always submits with ``force=True``
    (overwrite-on-click). Progress is read from durable ``TopicBrief`` columns.
    """
    return _create_topic_brief(topic_scope_id, force=force)
