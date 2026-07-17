import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, cache, celery
from models import init_default_data
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.staff import staff_bp
from routes.user import user_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configure Celery to use Flask app context and explicit broker settings
    celery.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/1'),
        result_backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1'),
        timezone=app.config.get('CELERY_TIMEZONE', 'Asia/Kolkata')
    )
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    # Ensure static export directory exists for CSV downloads
    export_dir = os.path.join(app.root_path, 'static', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Ensure generated_reports directory exists for Celery HTML/mail logs
    report_dir = os.path.join(app.root_path, 'generated_reports')
    os.makedirs(report_dir, exist_ok=True)

    @app.route('/api/exports/<filename>', methods=['GET'])
    def download_export_file(filename):
        """
        Serve generated CSV export files to the frontend download link.
        """
        export_directory = os.path.join(app.root_path, 'static', 'exports')
        if not os.path.exists(os.path.join(export_directory, filename)):
            return jsonify({'error': 'Export file not found or expired.'}), 404
        return send_from_directory(export_directory, filename, as_attachment=True)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        Simple health check endpoint to verify backend status.
        """
        return jsonify({'status': 'running', 'message': 'TMA Backend API is online.'}), 200

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Auto-initialize tables and pre-populate default Admin & sample data if not present
        db.create_all()
        init_default_data()
    print("--> TMA Backend API starting on http://127.0.0.1:5000")
    print("--> Pre-existing Admin: admin@tma.com / admin123")
    app.run(host='0.0.0.0', port=5000, debug=True)
