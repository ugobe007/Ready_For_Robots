from app.services.inbox_classifier import classify_inbox_folder


def test_classify_inbox_folder_customer_reply():
    folder = classify_inbox_folder(
        from_email="michael@chipotle.com",
        subject="Re: Robot job matches & feasibility review for Chipotle",
        body_text="Thanks Phelan, we'd like to see the 3D cell-feasibility simulation.",
    )
    assert folder == "main"


def test_classify_inbox_folder_filters_pythh():
    folder1 = classify_inbox_folder(
        from_email="hello@pythh.ai",
        subject="Portfolio Digest: 8 signals",
    )
    assert folder1 == "test"

    folder2 = classify_inbox_folder(
        from_email="ops@pythh.ai",
        subject="The Pythh Daily Brief — 2026-09-30",
    )
    assert folder2 == "test"


def test_classify_inbox_folder_filters_sendfox_and_orbital():
    folder1 = classify_inbox_folder(
        from_email="mail@sendfoxmail.com",
        subject="[Received] Today: Getting hired through PE & VC firms",
    )
    assert folder1 == "test"

    folder2 = classify_inbox_folder(
        from_email="daily@orbital-ai.com",
        subject="OrbitalAi — 5 matches expire October 4, 2026",
    )
    assert folder2 == "test"


def test_classify_inbox_folder_filters_internal_cal_learning_reports():
    folder = classify_inbox_folder(
        from_email="ops@readyforrobots.com",
        subject="Cal learning report — last 7d (0 positive replies)",
    )
    assert folder == "test"
