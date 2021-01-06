#!/user/bin/env python
import click
from app import create_app, db, forms
from tools import get_all_requests_from_log, play_actions

app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, forms=forms)


@app.cli.command()
def read_log():
    get_all_requests_from_log()


@app.cli.command()
def replay():
    play_actions(app)


if __name__ == "__main__":
    app.run()
