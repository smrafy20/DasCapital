def register_blueprints(app):
    from .auth_routes import auth_bp
    from .dashboard_routes import dashboard_bp
    from .money_routes import money_bp
    from .statement_routes import statement_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(money_bp)
    app.register_blueprint(statement_bp)
