from config import application, db
import views

if __name__ == "__main__":
    application.debug = True
    application.run()
    with application.app_context():
        db.create_all()
