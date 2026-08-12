"""Map PubMed EFetch XML to source_record and typed promote fields."""

from __future__ import annotations

from datetime import date
from typing import Any
from xml.etree import ElementTree as ET

_MONTH_NAMES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def map_efetch_xml(xml_text: str) -> dict[str, Any]:
    """Parse one PubmedArticle EFetch XML into a mapped inform payload."""
    root = ET.fromstring(xml_text)
    article = root.find(".//PubmedArticle")
    if article is None:
        raise ValueError("EFetch XML has no PubmedArticle")

    medline = article.find("MedlineCitation")
    article_el = None if medline is None else medline.find("Article")
    if medline is None or article_el is None:
        raise ValueError("EFetch XML missing MedlineCitation/Article")

    abstract = _map_abstract(article_el, medline)
    dates = _map_dates(article, medline, article_el)
    journal_detail = _map_journal_detail(medline, article_el)
    types_language = _map_types_language(medline, article_el)
    indexing = _map_indexing(medline)
    funding = _map_funding(article_el)
    coi_notes = _map_coi_notes(medline)

    title = _text(article_el.find("ArticleTitle")) or ""
    authors = _map_author_names(article_el)
    journal = (
        journal_detail.get("medline_ta")
        or _text(article_el.find("Journal/Title"))
        or None
    )
    pub_date_parts = dates.get("pub_date") or {}
    published_year = pub_date_parts.get("year")
    pub_date = _full_date(pub_date_parts)
    abstract_text = _join_abstract_parts(abstract.get("parts") or [])

    return {
        "source_record": {
            "abstract": abstract,
            "dates": dates,
            "journal_detail": journal_detail,
            "types_language": types_language,
            "indexing": indexing,
            "funding": funding,
            "coi_notes": coi_notes,
        },
        "title": title,
        "authors": authors,
        "journal": journal,
        "published_year": published_year,
        "pub_date": pub_date,
        "abstract_text": abstract_text,
    }


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    text = "".join(el.itertext()).strip()
    return text or None


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    month = _MONTH_NAMES.get(value[:3].lower())
    return month


def _ymd_from(parent: ET.Element | None) -> dict[str, int | None] | None:
    if parent is None:
        return None
    year = _parse_int(_text(parent.find("Year")))
    month = _parse_int(_text(parent.find("Month")))
    day = _parse_int(_text(parent.find("Day")))
    if year is None and month is None and day is None:
        return None
    return {"year": year, "month": month, "day": day}


def _full_date(parts: dict[str, int | None] | None) -> date | None:
    if not parts:
        return None
    year, month, day = parts.get("year"), parts.get("month"), parts.get("day")
    if year is None or month is None or day is None:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _map_abstract(article_el: ET.Element, medline: ET.Element) -> dict[str, Any]:
    parts: list[dict[str, str | None]] = []
    abstract_el = article_el.find("Abstract")
    if abstract_el is not None:
        for text_el in abstract_el.findall("AbstractText"):
            parts.append(
                {
                    "label": text_el.attrib.get("Label"),
                    "text": "".join(text_el.itertext()).strip(),
                }
            )
        copyright_info = _text(abstract_el.find("CopyrightInformation"))
    else:
        copyright_info = None

    other_abstracts: list[dict[str, Any]] = []
    for other in medline.findall("OtherAbstract"):
        other_parts = [
            {
                "label": text_el.attrib.get("Label"),
                "text": "".join(text_el.itertext()).strip(),
            }
            for text_el in other.findall("AbstractText")
        ]
        other_abstracts.append(
            {
                "language": other.attrib.get("Language"),
                "parts": other_parts,
            }
        )

    return {
        "parts": parts,
        "copyright": copyright_info,
        "other_abstracts": other_abstracts,
    }


def _join_abstract_parts(parts: list[dict[str, Any]]) -> str | None:
    texts = [str(part.get("text") or "").strip() for part in parts]
    texts = [t for t in texts if t]
    if not texts:
        return None
    return " ".join(texts)


def _map_dates(
    article: ET.Element,
    medline: ET.Element,
    article_el: ET.Element,
) -> dict[str, Any]:
    pub_date = _ymd_from(article_el.find("Journal/JournalIssue/PubDate"))
    article_date = None
    for ad in article_el.findall("ArticleDate"):
        if ad.attrib.get("DateType") == "Electronic" or article_date is None:
            article_date = _ymd_from(ad)
            if ad.attrib.get("DateType") == "Electronic":
                break

    history: list[dict[str, Any]] = []
    for hist in article.findall("PubmedData/History/PubMedPubDate"):
        parts = _ymd_from(hist) or {}
        history.append(
            {
                "pub_status": hist.attrib.get("PubStatus"),
                "year": parts.get("year"),
                "month": parts.get("month"),
                "day": parts.get("day"),
            }
        )

    return {
        "pub_date": pub_date,
        "article_date_electronic": article_date,
        "date_completed": _ymd_from(medline.find("DateCompleted")),
        "date_revised": _ymd_from(medline.find("DateRevised")),
        "history": history,
    }


def _map_journal_detail(
    medline: ET.Element,
    article_el: ET.Element,
) -> dict[str, Any]:
    journal = article_el.find("Journal")
    issue = None if journal is None else journal.find("JournalIssue")
    info = medline.find("MedlineJournalInfo")
    return {
        "issn": None if journal is None else _text(journal.find("ISSN")),
        "volume": None if issue is None else _text(issue.find("Volume")),
        "issue": None if issue is None else _text(issue.find("Issue")),
        "medline_pgn": _text(article_el.find("Pagination/MedlinePgn")),
        "iso_abbreviation": (
            None if journal is None else _text(journal.find("ISOAbbreviation"))
        ),
        "medline_ta": None if info is None else _text(info.find("MedlineTA")),
        "country": None if info is None else _text(info.find("Country")),
        "nlm_unique_id": None if info is None else _text(info.find("NlmUniqueID")),
        "issn_linking": None if info is None else _text(info.find("ISSNLinking")),
    }


def _map_types_language(
    medline: ET.Element,
    article_el: ET.Element,
) -> dict[str, Any]:
    pub_types = [
        t
        for t in (
            _text(el) for el in article_el.findall("PublicationTypeList/PublicationType")
        )
        if t
    ]
    languages = [
        t for t in (_text(el) for el in article_el.findall("Language")) if t
    ]
    return {
        "publication_types": pub_types,
        "languages": languages,
        "pub_model": article_el.attrib.get("PubModel"),
        "medline_status": medline.attrib.get("Status"),
        "medline_owner": medline.attrib.get("Owner"),
    }


def _map_indexing(medline: ET.Element) -> dict[str, Any]:
    mesh_headings: list[dict[str, Any]] = []
    for heading in medline.findall("MeshHeadingList/MeshHeading"):
        descriptor = heading.find("DescriptorName")
        qualifiers = []
        for qual in heading.findall("QualifierName"):
            qualifiers.append(
                {
                    "name": _text(qual),
                    "major_topic": qual.attrib.get("MajorTopicYN") == "Y",
                }
            )
        mesh_headings.append(
            {
                "descriptor": _text(descriptor),
                "major_topic": (
                    descriptor.attrib.get("MajorTopicYN") == "Y"
                    if descriptor is not None
                    else False
                ),
                "qualifiers": qualifiers,
            }
        )

    keywords = [
        t
        for t in (
            _text(el) for el in medline.findall("KeywordList/Keyword")
        )
        if t
    ]
    chemicals = []
    for chem in medline.findall("ChemicalList/Chemical"):
        chemicals.append(
            {
                "name": _text(chem.find("NameOfSubstance")),
                "registry_number": _text(chem.find("RegistryNumber")),
            }
        )
    suppl_mesh = [
        t
        for t in (
            _text(el) for el in medline.findall("SupplMeshList/SupplMeshName")
        )
        if t
    ]
    citation_subsets = [
        t for t in (_text(el) for el in medline.findall("CitationSubset")) if t
    ]
    return {
        "mesh_headings": mesh_headings,
        "keywords": keywords,
        "chemicals": chemicals,
        "suppl_mesh": suppl_mesh,
        "citation_subsets": citation_subsets,
    }


def _map_funding(article_el: ET.Element) -> dict[str, Any]:
    grants = []
    for grant in article_el.findall("GrantList/Grant"):
        grants.append(
            {
                "agency": _text(grant.find("Agency")),
                "country": _text(grant.find("Country")),
                "grant_id": _text(grant.find("GrantID")),
            }
        )
    databanks = []
    for bank in article_el.findall("DataBankList/DataBank"):
        accession_numbers = [
            t
            for t in (
                _text(el)
                for el in bank.findall("AccessionNumberList/AccessionNumber")
            )
            if t
        ]
        databanks.append(
            {
                "name": _text(bank.find("DataBankName")),
                "accession_numbers": accession_numbers,
            }
        )
    return {"grants": grants, "databanks": databanks}


def _map_coi_notes(medline: ET.Element) -> dict[str, Any]:
    notes = [
        t for t in (_text(el) for el in medline.findall("GeneralNote")) if t
    ]
    return {
        "coi_statement": _text(medline.find("CoiStatement")),
        "general_notes": notes,
    }


def _map_author_names(article_el: ET.Element) -> list[str]:
    names: list[str] = []
    for author in article_el.findall("AuthorList/Author"):
        collective = _text(author.find("CollectiveName"))
        if collective:
            names.append(collective)
            continue
        last = _text(author.find("LastName"))
        initials = _text(author.find("Initials"))
        fore = _text(author.find("ForeName"))
        if last and initials:
            names.append(f"{last} {initials}")
        elif last and fore:
            names.append(f"{last} {fore}")
        elif last:
            names.append(last)
    return names
