from app import create_app

app = create_app()

if __name__ == "__main__":
    # Bind to localhost only in development.
    # PythonAnywhere uses wsgi.py — this block never runs there.
    app.run(host="127.0.0.1", port=5000, debug=True)
