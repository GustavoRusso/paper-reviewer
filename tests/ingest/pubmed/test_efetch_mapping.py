"""PubMed EFetch XML → mapped source_record and typed promotes."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from paper_reviewer.ingest.pubmed.efetch_mapping import map_efetch_xml

FIXTURE = Path(__file__).parent / "fixtures" / "efetch_sample.xml"


def test_map_efetch_xml_builds_source_record_and_promotes() -> None:
    xml = FIXTURE.read_text(encoding="utf-8")

    mapped = map_efetch_xml(xml)

    assert mapped["title"] == "Enzyme replacement in Gaucher disease"
    assert mapped["authors"] == ["Smith J", "Doe A"]
    assert mapped["journal"] == "Orphanet J Rare Dis"
    assert mapped["published_year"] == 2024
    assert mapped["pub_date"] == date(2024, 3, 15)
    assert mapped["abstract_text"] == (
        "Gaucher disease is a lysosomal storage disorder. "
        "We reviewed 42 consecutive patients."
    )

    record = mapped["source_record"]
    assert record["abstract"]["parts"][0]["label"] == "BACKGROUND"
    assert record["dates"]["pub_date"] == {"year": 2024, "month": 3, "day": 15}
    assert record["journal_detail"]["issn"] == "1234-5678"
    assert record["journal_detail"]["volume"] == "18"
    assert record["types_language"]["languages"] == ["eng"]
    assert record["indexing"]["mesh_headings"][0]["descriptor"] == "Gaucher Disease"
    assert record["indexing"]["keywords"] == ["lysosomal storage"]
    assert record["funding"]["grants"][0]["grant_id"] == "R01EX123456"
    assert "no competing interests" in record["coi_notes"]["coi_statement"]
