from app.models.schemas import SupervisorDecision


def test_supervisor_decision_schema():
    result = SupervisorDecision(
        issue="Test issue",
        worker_can_resolve=True,
        confidence=0.9,
        troubleshooting_message="Check the displayed alarm.",
    )
    assert result.worker_can_resolve is True
    assert result.confidence == 0.9
