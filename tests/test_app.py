from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app



@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@example.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.post(
        "/activities/Unknown%20Activity/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_participant_removes_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@example.edu"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/Chess%20Club/participants/{email}"
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }


def test_unregister_unknown_participant_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    email = "missing@example.edu"

    # Act
    response = client.delete(
        f"/activities/Chess%20Club/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}


def test_unregister_from_unknown_activity_returns_404(client):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.delete(
        f"/activities/Unknown%20Activity/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
