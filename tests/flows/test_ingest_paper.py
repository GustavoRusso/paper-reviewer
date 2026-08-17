"""ingest_paper parent flow: subflows with force, skip brief when needed."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pytest

from paper_reviewer.flows.ingest_paper import ingest_paper
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    InformFullTextResult,
    InformSourceRecordResult,
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    CreatePaperBriefResult,
)

_DOI = "10.1000/EXAMPLE"
_PAPER_ID = 42
_INGEST_MOD = importlib.import_module("paper_reviewer.flows.ingest_paper")


def _patch_subflows(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mock_src: MagicMock,
    mock_ft: MagicMock,
    mock_brief: MagicMock,
) -> None:
    monkeypatch.setattr(_INGEST_MOD, "inform_source_record", mock_src)
    monkeypatch.setattr(_INGEST_MOD, "inform_full_text", mock_ft)
    monkeypatch.setattr(_INGEST_MOD, "create_paper_brief", mock_brief)


def test_ingest_paper_calls_subflows_with_force(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = InformSourceRecordResult(
        paper_id=_PAPER_ID,
        status=PaperAspectStatus.succeeded,
    )
    full_text = InformFullTextResult(
        paper_id=_PAPER_ID,
        status=PaperAspectStatus.succeeded,
    )
    brief = CreatePaperBriefResult(
        paper_id=_PAPER_ID,
        status=PaperAspectStatus.succeeded,
    )
    mock_src = MagicMock(return_value=source)
    mock_ft = MagicMock(return_value=full_text)
    mock_brief = MagicMock(return_value=brief)
    _patch_subflows(
        monkeypatch,
        mock_src=mock_src,
        mock_ft=mock_ft,
        mock_brief=mock_brief,
    )

    result = ingest_paper.fn(_PAPER_ID, _DOI)

    mock_src.assert_called_once_with(_PAPER_ID, _DOI, force=True)
    mock_ft.assert_called_once_with(_PAPER_ID, _DOI, force=True)
    mock_brief.assert_called_once_with(_PAPER_ID, _DOI, force=True)
    assert result.paper_id == _PAPER_ID
    assert result.source_record is source
    assert result.full_text is full_text
    assert result.brief is brief


def test_ingest_paper_skips_brief_when_full_text_not_succeeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = InformSourceRecordResult(
        paper_id=_PAPER_ID,
        status=PaperAspectStatus.succeeded,
    )
    full_text = InformFullTextResult(
        paper_id=_PAPER_ID,
        status=PaperAspectStatus.unavailable,
    )
    mock_src = MagicMock(return_value=source)
    mock_ft = MagicMock(return_value=full_text)
    mock_brief = MagicMock()
    _patch_subflows(
        monkeypatch,
        mock_src=mock_src,
        mock_ft=mock_ft,
        mock_brief=mock_brief,
    )

    result = ingest_paper.fn(_PAPER_ID, _DOI)

    mock_src.assert_called_once_with(_PAPER_ID, _DOI, force=True)
    mock_ft.assert_called_once_with(_PAPER_ID, _DOI, force=True)
    mock_brief.assert_not_called()
    assert result.brief is None
    assert result.full_text.status is PaperAspectStatus.unavailable
