from app.services.chunking import chunk_text

def test_short_test_is_one_chunk():
    assert chunk_text("hello world") == ["hello world"]

def test_empty_text_gives_no_chunk():
    assert chunk_text("") == []

def text_chunks_respect_size():
    text = "a" * 1200
    chunks = chunk_text(text, size=500, overlap=50)
    assert len(chunks) == 3
    assert all( len(c) <= 500 for c in chunks )