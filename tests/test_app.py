import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def sample_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["student@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(sample_activities):
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, sample_activities):
    # Arrange
    expected_activities = sample_activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, sample_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in sample_activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, sample_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    original_participants = sample_activities[activity_name]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert sample_activities[activity_name]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client, sample_activities):
    # Arrange
    original_activities = sample_activities.copy()

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert sample_activities == original_activities


def test_unregister_removes_participant(client, sample_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in sample_activities[activity_name]["participants"]


def test_unregister_rejects_nonparticipant(client, sample_activities):
    # Arrange
    activity_name = "Chess Club"
    original_participants = sample_activities[activity_name]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert sample_activities[activity_name]["participants"] == original_participants


def test_unregister_rejects_unknown_activity(client, sample_activities):
    # Arrange
    original_activities = sample_activities.copy()

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert sample_activities == original_activities