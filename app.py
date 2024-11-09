from flask import Flask, render_template, jsonify
from compute import compute
from db import init_db, get_results
import logging

logging.basicConfig(level=logging.INFO)

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.from_mapping(test_config)    
    else:
        app.config.from_mapping(DATABASE='database.db')

    app.register_blueprint(compute)

    @app.route('/')
    def index():
        return render_template('admin.html')

    @app.route('/api/results')
    def results():
        results = get_results(app.config['DATABASE'])
        return jsonify(results)

    return app

if __name__ == '__main__':
    app = create_app()
    init_db(app.config['DATABASE'])
    app.run(debug=True)
