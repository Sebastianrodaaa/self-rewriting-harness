from runtime.checker import check_response, extract_answer_line


def test_extract_answer_line():
    assert extract_answer_line("foo\nANSWER: 15\n") == "ANSWER: 15"


def test_check_exact():
    ok, _ = check_response("ANSWER: 15", "thinking...\nANSWER: 15")
    assert ok
    ok2, reason = check_response("ANSWER: 15", "ANSWER: 16")
    assert not ok2
    assert "expected" in reason
