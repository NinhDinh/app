from server import create_app, fake_data

app = create_app()

with app.app_context():
    fake_data()
