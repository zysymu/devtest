def test_create_demand(client):
    response = client.post('/demand', json={'floor': 3})
    assert response.status_code == 201
    assert response.get_json() == {'message': 'Demand created'}


def test_create_state(client):
    response = client.post('/state', json={'floor': 5, 'vacant': True})
    assert response.status_code == 201
    assert response.get_json() == {'message': 'State created'}
