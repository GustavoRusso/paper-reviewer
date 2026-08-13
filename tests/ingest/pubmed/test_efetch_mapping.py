"""PubMed EFetch XML → mapped source_record and typed promotes."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from paper_reviewer.ingest.pubmed.efetch_mapping import map_efetch_xml

FIXTURE = Path(__file__).parent / "fixtures" / "efetch_sample.xml"

_MINIMAL_ARTICLE = """\
<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">100</PMID>
      <Article PubModel="Print">
        <Journal>
          <JournalIssue CitedMedium="Print">
            <PubDate><Year>2024</Year></PubDate>
          </JournalIssue>
          <Title>Example</Title>
        </Journal>
        <ArticleTitle>Minimal article</ArticleTitle>
        <AuthorList CompleteYN="Y">
          <Author ValidYN="Y">
            <LastName>Smith</LastName>
            <Initials>J</Initials>
          </Author>
        </AuthorList>
        <Language>eng</Language>
      </Article>
    </MedlineCitation>
    <PubmedData>
      {article_id_list}
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


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
    assert mapped["pmcid"] == "PMC5334499"

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
    assert "article_ids" not in record
    assert "ArticleIdList" not in record


def test_map_efetch_xml_pmcid_null_when_article_id_list_missing() -> None:
    xml = _MINIMAL_ARTICLE.format(article_id_list="")

    mapped = map_efetch_xml(xml)

    assert mapped["pmcid"] is None


def test_map_efetch_xml_pmcid_null_when_only_non_pmc_ids() -> None:
    xml = _MINIMAL_ARTICLE.format(
        article_id_list=(
            "<ArticleIdList>"
            '<ArticleId IdType="pubmed">100</ArticleId>'
            '<ArticleId IdType="doi">10.1234/example</ArticleId>'
            "</ArticleIdList>"
        )
    )

    mapped = map_efetch_xml(xml)

    assert mapped["pmcid"] is None


def test_map_efetch_xml_normalizes_pmcid_without_prefix() -> None:
    xml = _MINIMAL_ARTICLE.format(
        article_id_list=(
            "<ArticleIdList>"
            '<ArticleId IdType="pmc">5334499</ArticleId>'
            "</ArticleIdList>"
        )
    )

    mapped = map_efetch_xml(xml)

    assert mapped["pmcid"] == "PMC5334499"


def test_map_efetch_xml_accepts_lowercase_idtype_attribute() -> None:
    xml = _MINIMAL_ARTICLE.format(
        article_id_list=(
            "<ArticleIdList>"
            '<ArticleId idtype="pmc">PMC11370360</ArticleId>'
            "</ArticleIdList>"
        )
    )

    mapped = map_efetch_xml(xml)

    assert mapped["pmcid"] == "PMC11370360"
