from flask import Flask, render_template, redirect, request, jsonify
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic, UserActivity
from datetime import datetime
import webbrowser
import threading
import os

# Initialize Flask App
# Handle resource paths for PyInstaller (frozen) vs Development
import sys

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    base_dir = os.path.join(sys._MEIPASS, 'glint', 'web')
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route('/')
def dashboard():
    """Render the main dashboard or prompt page on first run."""
    topic_filter = request.args.get('topic')
    category_filter = request.args.get('category')
    
    engine = get_engine()
    with Session(engine) as session:
        # Check if topics exist
        topics = session.exec(select(Topic)).all()
        if not topics:
            return render_template('prompt.html')
        
        # Build query with filters
        query = (
            select(Trend, Topic.name)
            .join(Topic)
            .where(Trend.status == 'approved')
        )
        
        # Apply topic filter
        if topic_filter:
            query = query.where(Topic.name == topic_filter)
        
        # Apply category filter
        if category_filter:
            if category_filter == 'news':
                query = query.where(Trend.category == 'news')
            elif category_filter == 'tools':
                query = query.where(Trend.category.in_(['tool', 'repo', 'product']))
        
        # Execute query
        statement = query.order_by(Trend.published_at.desc()).limit(50)
        results = session.exec(statement).all()
        
        # Format trends with topic names
        trends_data = []
        for trend, topic_name in results:
            trends_data.append({
                'id': trend.id,
                'title': trend.title,
                'description': trend.description,
                'source': trend.source,
                'published_at': trend.published_at,
                'topic_name': topic_name,
                'category': trend.category
            })
        
        return render_template('dashboard.html', 
                             trends=trends_data, 
                             topics=topics,
                             current_topic=topic_filter,
                             current_category=category_filter)

@app.route('/setup', methods=['POST'])
def setup():
    """Handle first-run topic submission."""
    topics_str = request.form.get('topics', '')
    if not topics_str:
        return redirect('/')
    
    # Parse and save topics
    topic_names = [t.strip() for t in topics_str.split(',') if t.strip()]
    engine = get_engine()
    with Session(engine) as session:
        for name in topic_names:
            existing = session.exec(select(Topic).where(Topic.name == name)).first()
            if not existing:
                session.add(Topic(name=name, is_active=True))
        session.commit()
    
    # Run initial fetch
    try:
        from glint.cli.commands.fetch import fetch
        fetch()
    except Exception as e:
        print(f"Fetch error: {e}")
    
    return redirect('/')

@app.route('/cmd', methods=['POST'])
def execute_command():
    """Execute a CLI command and return output."""
    import io
    import sys
    
    cmd_str = request.json.get('command', '').strip()
    if not cmd_str:
        return jsonify({"output": "No command provided"})
    
    # Parse command
    parts = cmd_str.split()
    if not parts:
        return jsonify({"output": "Invalid command"})
    
    cmd_name = parts[0]
    args = parts[1:]
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        # Route to appropriate command
        if cmd_name == 'status':
            from glint.cli.commands.status import status
            status()
        elif cmd_name == 'add' and args:
            from glint.cli.commands.topics import add
            add(topic_name=' '.join(args))
        elif cmd_name == 'remove' and args:
            from glint.cli.commands.topics import remove
            remove(topic_name=' '.join(args))
        elif cmd_name == 'fetch':
            from glint.cli.commands.fetch import fetch
            fetch()
        elif cmd_name == 'list':
            from glint.cli.commands.topics import list_topics
            list_topics()
        else:
            output = f"Unknown command: {cmd_name}"
            sys.stdout = old_stdout
            return jsonify({"output": output})
        
        output = captured_output.getvalue()
    except Exception as e:
        output = f"Error: {str(e)}"
    finally:
        sys.stdout = old_stdout
    
    return jsonify({"output": output})

@app.route('/trend/<int:trend_id>')
def view_trend(trend_id):
    """View a specific trend and log the activity."""
    engine = get_engine()
    with Session(engine) as session:
        trend = session.get(Trend, trend_id)
        if not trend:
            return "Trend not found", 404
            
        # Log Activity
        activity = UserActivity(
            trend_id=trend.id,
            clicked_at=datetime.utcnow()
        )
        session.add(activity)
        
        # Mark trend as read (optional, but good UX)
        trend.is_read = True
        session.add(trend)
        
        session.commit()
        
        # Redirect to actual content
        return redirect(trend.url)

def start_server(port=5000, debug=False):
    """Start the Flask server."""
    # Disable Flask banner to keep CLI clean
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='127.0.0.1', port=port, debug=debug, use_reloader=False)

def open_dashboard(port=5000):
    """Open the dashboard in the default browser."""
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    start_server(debug=True)
