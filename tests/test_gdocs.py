from engine.gdocs import GoogleDocsClient


def test_chunk_content():
    client = GoogleDocsClient()
    short_text = "Line 1\nLine 2\nLine 3"
    chunks = client._chunk_content(short_text, max_size=50)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    long_text = "\n".join([f"This is line number {i} of the document" for i in range(100)])
    chunks_long = client._chunk_content(long_text, max_size=200)
    assert len(chunks_long) > 1
    # Check that recombined text equals original
    assert "".join(chunks_long) == long_text


def test_dry_run_sync():
    client = GoogleDocsClient()
    res = client.sync_markdown_to_doc(
        doc_id="test_doc_123",
        content="# Test Header\n\nSome body content here.",
        dry_run=True
    )
    assert res["success"] is True
    assert res["dry_run"] is True
    assert res["doc_id"] == "test_doc_123"
    assert res["chars_synced"] > 0
