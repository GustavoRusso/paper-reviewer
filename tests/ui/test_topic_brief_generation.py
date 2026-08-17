"""Topic brief generation landing: registration, helpers, and copy."""

from __future__ import annotations

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
)
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_brief_generation import (
    GENERATE_TOPIC_BRIEF_LABEL,
    GENERATING_STATUS_LABEL,
    GO_TO_PAPER_ARCHIVING_LABEL,
    GO_TO_SHOW_REFERENCES_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    REGENERATE_TOPIC_BRIEF_LABEL,
    SUCCEEDED_STATUS_LABEL,
    ZERO_BRIEFED_CAPTION,
    doi_content_url,
    generate_button_enabled,
    generate_button_label,
    is_in_flight,
    parse_stored_topic_brief_content,
    render_topic_brief_generation,
    should_render_topic_brief_content,
    split_topic_brief_error_message,
)
from tests.topic_scope.topic_brief_generation.helpers import (
    sample_topic_brief_content,
)


def test_render_topic_brief_generation_is_public() -> None:
    assert callable(render_topic_brief_generation)


def test_topic_brief_generation_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["topic_brief_generation"].render is render_topic_brief_generation
    assert pages["topic_brief_generation"].title == "Topic brief generation"
    assert pages["topic_brief_generation"].url_path == "topic-brief-generation"
    assert pages["topic_brief_generation"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Topic brief "
        "generation from the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_zero_briefed_caption_and_helpful_links() -> None:
    assert ZERO_BRIEFED_CAPTION == (
        "Generation needs at least one Reference with a succeeded paper brief."
    )
    assert GO_TO_SHOW_REFERENCES_LABEL == "Go to Show references"
    assert GO_TO_PAPER_ARCHIVING_LABEL == "Go to Paper archiving"


def test_button_and_status_labels() -> None:
    assert GENERATE_TOPIC_BRIEF_LABEL == "Generate topic brief"
    assert REGENERATE_TOPIC_BRIEF_LABEL == "Regenerate topic brief"
    assert GENERATING_STATUS_LABEL == "Generating topic brief…"
    assert SUCCEEDED_STATUS_LABEL == "Topic brief ready"


def test_generate_button_label_depends_on_stored_content() -> None:
    assert generate_button_label(has_content=False) == GENERATE_TOPIC_BRIEF_LABEL
    assert generate_button_label(has_content=True) == REGENERATE_TOPIC_BRIEF_LABEL


def test_generate_button_disabled_when_zero_briefed() -> None:
    assert generate_button_enabled(briefed_count=0, status=None) is False
    assert (
        generate_button_enabled(
            briefed_count=0,
            status=PaperAspectStatus.succeeded,
        )
        is False
    )


def test_generate_button_disabled_when_in_flight() -> None:
    assert (
        generate_button_enabled(
            briefed_count=1,
            status=PaperAspectStatus.not_started,
        )
        is False
    )
    assert is_in_flight(PaperAspectStatus.not_started) is True
    assert is_in_flight(PaperAspectStatus.succeeded) is False
    assert is_in_flight(None) is False


def test_generate_button_enabled_when_idle_with_briefed() -> None:
    assert generate_button_enabled(briefed_count=1, status=None) is True
    assert (
        generate_button_enabled(
            briefed_count=2,
            status=PaperAspectStatus.succeeded,
        )
        is True
    )
    assert (
        generate_button_enabled(
            briefed_count=1,
            status=PaperAspectStatus.failed,
        )
        is True
    )


def test_should_render_content_when_succeeded_or_failed_with_content() -> None:
    assert (
        should_render_topic_brief_content(
            status=PaperAspectStatus.succeeded,
            has_content=True,
        )
        is True
    )
    assert (
        should_render_topic_brief_content(
            status=PaperAspectStatus.failed,
            has_content=True,
        )
        is True
    )
    assert (
        should_render_topic_brief_content(
            status=PaperAspectStatus.failed,
            has_content=False,
        )
        is False
    )
    assert (
        should_render_topic_brief_content(
            status=PaperAspectStatus.not_started,
            has_content=True,
        )
        is False
    )
    assert (
        should_render_topic_brief_content(status=None, has_content=False) is False
    )


def test_split_topic_brief_error_message_without_dump() -> None:
    caption, dump = split_topic_brief_error_message("llm down")
    assert caption == "llm down"
    assert dump is None


def test_split_topic_brief_error_message_with_dump() -> None:
    caption, dump = split_topic_brief_error_message(
        "bad json\n\nAssistant output:\n{not-json}"
    )
    assert caption == "bad json"
    assert dump == "{not-json}"


def test_doi_content_url() -> None:
    assert doi_content_url("10.1000/abc") == "https://doi.org/10.1000/abc"
    assert doi_content_url("10.1000/ABC") == "https://doi.org/10.1000/ABC"


def test_parse_stored_topic_brief_content() -> None:
    payload = sample_topic_brief_content().model_dump(mode="json")
    parsed = parse_stored_topic_brief_content(payload)
    assert isinstance(parsed, TopicBriefContent)
    assert parsed.title == sample_topic_brief_content().title
    assert parse_stored_topic_brief_content(None) is None
    assert parse_stored_topic_brief_content({"title": "only"}) is None
