def test_home_page(client):
    response = client.get('/')
    content = response.data.decode('utf-8')
    assert "Лоты" in content or "Аукцион" in content

