from flask import Flask, render_template

def create_app():
    app = Flask(__name__,
                static_url_path = '')       

    @app.route('/')
    def index():
        return render_template('base.html')

    return app


if __name__ == '__main__':
    debug_app = create_app()
    debug_app.run()
