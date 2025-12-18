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
        # Check if topics exist and they active
        topics = session.exec(select(Topic).where(Topic.is_active == True)).all()
        if not topics:
            # If no topics, show prompt page to add topics
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
        
    # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # Get total count for pagination
        from sqlmodel import func
        count_statement = select(func.count()).select_from(query.subquery())
        total_trends = session.exec(count_statement).one()
        total_pages = (total_trends + per_page - 1) // per_page
        
        # Execute query with pagination
        statement = query.order_by(Trend.published_at.desc()).offset(offset).limit(per_page)
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
                             current_category=category_filter,
                             current_page=page,
                             total_pages=total_pages)

@app.route('/trend/<int:trend_id>/delete', methods=['POST'])
def delete_trend(trend_id):
    """Delete a specific trend."""
    engine = get_engine()
    with Session(engine) as session:
        trend = session.get(Trend, trend_id)
        if not trend:
            return jsonify({"success": False, "error": "Trend not found"}), 404
            
        session.delete(trend)
        session.commit()
        return jsonify({"success": True})

@app.route('/setup', methods=['POST'])
def setup():
    """Handle first-run topic submission."""
    topics_str = request.form.get('topics', '')
    if not topics_str:
        return redirect('/')
    
    # Parse and save topics
    topic_names = [topic.strip() for topic in topics_str.split(',') if topic.strip()]
    engine = get_engine()
    with Session(engine) as session:
        for topic_name in topic_names:
            existing = session.exec(select(Topic).where(Topic.name == topic_name)).first()
            if not existing:
                session.add(Topic(name=topic_name, is_active=True))
        session.commit()
    
    # Run initial fetch
    try:
        from glint.cli.commands.fetch import fetch
        fetch()
    except Exception as e:
        print(f"Fetch error: {e}")
    
    return redirect('/')

def show_help():
    """Return a formatted help string for the web command panel."""
    return """
Available Commands:
  fetch                Fetch latest trends from all sources
  status               Show current system status
  list                 List all watched topics
  add <topic>          Add a new topic to watch
  clear                Clear the command output
  
  config schedule show          Show notification schedule
  config schedule set <H:M> <H:M>  Set notification schedule
  
  config topics list            List all topics with status
  config topics toggle <name>   Enable/Disable a topic
  config topics delete <name>   Permanently delete a topic
  
  config secrets show           Show configured API keys (masked)
  config secrets set <k> <v>    Set an API key (e.g., devto, producthunt)

  help, --help         Show this help message
"""

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
    
    # Handle help
    if cmd_name in ['help', '--help']:
        return jsonify({"output": show_help()})
    
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
            add(topic_name=' '.join(args).lower())
        elif cmd_name == 'fetch':
            from glint.cli.commands.fetch import fetch
            fetch()
        elif cmd_name == 'list':
            from glint.cli.commands.topics import list_topics
            list_topics()
        elif cmd_name == 'clear':
            # return special output to tell frontend to clear
            sys.stdout = old_stdout
            return jsonify({"output": "", "action": "clear"})
        elif cmd_name == 'config':
            from glint.cli.commands.config import show_schedule, set_schedule, list_topics, toggle_topic, delete_topic, show_secrets, set_secret
            
            if len(args) >= 1:
                subcmd = args[0]
                
                # config schedule ...
                if subcmd == 'schedule':
                    if len(args) == 2 and args[1] == 'show':
                        show_schedule()
                    elif len(args) == 4 and args[1] == 'set':
                        set_schedule(start=args[2], end=args[3])
                    else:
                        print("Usage: config schedule show OR config schedule set HH:MM HH:MM")
                
                # config topics ...
                elif subcmd == 'topics':
                    if len(args) == 2 and args[1] == 'list':
                        list_topics()
                    elif len(args) >= 3 and args[1] == 'toggle':
                        toggle_topic(name=' '.join(args[2:]))
                    elif len(args) >= 3 and args[1] == 'delete':
                        # Force delete via web UI to avoid interactive prompt issues
                        delete_topic(name=' '.join(args[2:]), force=True)
                    else:
                        print("Usage: config topics list, config topics toggle <name>, config topics delete <name>")
                
                # config secrets ...
                elif subcmd == 'secrets':
                    if len(args) == 2 and args[1] == 'show':
                        show_secrets()
                    elif len(args) == 4 and args[1] == 'set':
                        set_secret(key=args[2], value=args[3])
                    else:
                        print("Usage: config secrets show OR config secrets set <key> <value>")
                
                else:
                    print(f"Unknown config subcommand: {subcmd}")
                    print("Available: schedule, topics, secrets")
            else:
                print("Available config commands:\n  config schedule [show|set]\n  config topics [list|toggle|delete]\n  config secrets [show|set]")

        else:
            # If command unknown, show help
            sys.stdout = old_stdout
            return jsonify({"output": f"Unknown command: {cmd_name}\n" + show_help()})
        
        # Get output and strip ANSI codes
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        raw_output = captured_output.getvalue()
        output = ansi_escape.sub('', raw_output)
        
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
    
    # Start continuous fetching in the background (2-hour interval)
    try:
        from glint.core.notifier import Notifier
        notifier = Notifier(interval_seconds=7200)
        notifier.start()
        print(f"[*] Continuous fetching enabled (Interval: 2h)")
    except Exception as e:
        print(f"[!] Could not start continuous fetching: {e}")
    
    app.run(host='127.0.0.1', port=port, debug=debug, use_reloader=False)

def open_dashboard(port=5000):
    """Open the dashboard in the default browser."""
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    start_server(debug=True)
