from evidence_dossier.model import make_document_id, make_section_id, make_work_id


def test_work_id_is_stable_for_the_same_source_identity() -> None:
    # sha256("pmid:12345678") starts with 4f4402cd240d30fe.
    assert make_work_id("pmid", "90000001") == "work_4f4402cd240d30fe"


def test_work_id_depends_on_the_identifier_scheme() -> None:
    # sha256("arxiv:9901.00001") starts with 862e86582f0a447a.
    assert make_work_id("arxiv", "9901.00001") == "work_862e86582f0a447a"
    assert make_work_id("pmid", "2401") != make_work_id("arxiv", "2401")


def test_document_and_section_ids_extend_the_work_id() -> None:
    document_id = make_document_id("work_4f4402cd240d30fe", version=2)

    assert document_id == "work_4f4402cd240d30fe_v2"
    assert make_section_id(document_id, ordinal=3) == "work_4f4402cd240d30fe_v2_s3"
