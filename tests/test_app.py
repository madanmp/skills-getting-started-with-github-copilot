from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_state(monkeypatch):
    state = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", state)
    return state


@pytest.fixture
def client(activity_state):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_data_without_caching(client, activity_state):
    # Arrange
    expected_activities = activity_state

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, activity_state):
    # Arrange
    activity_name = "Art Club"
    email = "student@mergington.edu"
    expected_participants = activity_state[activity_name]["participants"] + [email]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activity_state[activity_name]["participants"] == expected_participants


def test_signup_rejects_duplicate_participant(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = activity_state[activity_name]["participants"][0]
    expected_participants = activity_state[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert activity_state[activity_name]["participants"] == expected_participants


def test_signup_rejects_unknown_activity(client, activity_state):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    expected_activities = deepcopy(activity_state)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_state == expected_activities


def test_unregister_removes_participant(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = activity_state[activity_name]["participants"][0]
    expected_participants = activity_state[activity_name]["participants"][1:]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert activity_state[activity_name]["participants"] == expected_participants


def test_unregister_rejects_missing_participant(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = "not-signed-up@mergington.edu"
    expected_participants = activity_state[activity_name]["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_state[activity_name]["participants"] == expected_participants


def test_unregister_rejects_unknown_activity(client, activity_state):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    expected_activities = deepcopy(activity_state)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_state == expected_activities