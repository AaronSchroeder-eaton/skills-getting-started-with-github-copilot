import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original)


def test_get_activities_returns_activities():
    # Arrange
    with client:
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "participants" in data["Chess Club"]
        assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    # Arrange
    email = "newstudent@example.com"
    activity_name = "Chess Club"

    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    with client:
        # Act
        response = client.post(
            f"/activities/{encoded_activity}/signup?email={encoded_email}"
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["message"] == f"Signed up {email} for {activity_name}"

        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]


def test_duplicate_signup_returns_400():
    # Arrange
    email = "duplicate@example.com"
    activity_name = "Chess Club"

    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    with client:
        first_response = client.post(
            f"/activities/{encoded_activity}/signup?email={encoded_email}"
        )
        assert first_response.status_code == 200

        # Act
        second_response = client.post(
            f"/activities/{encoded_activity}/signup?email={encoded_email}"
        )

        # Assert
        assert second_response.status_code == 400
        assert second_response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant_success():
    # Arrange
    email = "remove@example.com"
    activity_name = "Programming Class"

    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    with client:
        signup_response = client.post(
            f"/activities/{encoded_activity}/signup?email={encoded_email}"
        )
        assert signup_response.status_code == 200

        # Act
        delete_response = client.delete(
            f"/activities/{encoded_activity}/participants?email={encoded_email}"
        )

        # Assert
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == f"Unregistered {email} from {activity_name}"

        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]


def test_remove_participant_from_missing_activity_returns_404():
    # Arrange
    email = "missing@example.com"
    activity_name = "Nonexistent Club"

    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    with client:
        # Act
        response = client.delete(
            f"/activities/{encoded_activity}/participants?email={encoded_email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    email = "notfound@example.com"
    activity_name = "Chess Club"

    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    with client:
        # Act
        response = client.delete(
            f"/activities/{encoded_activity}/participants?email={encoded_email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
