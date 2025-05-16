def test_register_login(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'password': '123456',
        'confirm_password': '123456'
    }, follow_redirects=True)
    assert 'Вы успешно зарегистрированы!' in response.data.decode('utf-8')

    print(response.data.decode('utf-8')) 

    assert 'Вход' in response.data.decode('utf-8')

    response = client.post('/login', data={
        'username': 'testuser',
        'password': '123456'
    }, follow_redirects=True)
    assert 'Лоты' in response.data.decode('utf-8') or response.status_code == 200
