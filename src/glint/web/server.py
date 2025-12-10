from flask import Flask, render_template, redirect, request, jsonify
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic, UserActivity
from datetime import datetime
import webbrowser
import threading
import os

# Initialize Flask App
# We need to specify template and static folders relative to this file
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

def get_db_session():
    engine = get_engine()
    return Session(engine)

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    topic_filter = request.args.get('topic')
    category_filter = request.args.get('category')

    with get_db_session() as session:
        # Fetch active topics for filter
        topics = session.exec(select(Topic).where(Topic.is_active == True)).all()
        
        # Base query
        query = (
            select(Trend, Topic.name)
            .join(Topic)
            .where(Trend.status == "approved")
        )

        # Apply Topic filter
        if topic_filter:
            query = query.where(Topic.name == topic_filter)
            
        # Apply Category filter
        if category_filter:
            if category_filter == 'news':
                query = query.where(Trend.category == 'news')
            elif category_filter == 'tools':
                query = query.where(Trend.category.in_(['tool', 'repo', 'product']))

        # Finish query
        statement = query.order_by(Trend.published_at.desc()).limit(50)
        
        results = session.exec(statement).all()
        
        trends_data = []
        for trend, topic_name in results:
            trends_data.append({
                "id": trend.id,
                "title": trend.title,
                "description": trend.description,
                "source": trend.source,
                "published_at": trend.published_at.strftime("%Y-%m-%d %H:%M"),
                "topic": topic_name,
                "category": trend.category,
                "url": trend.url,
                "score": round(trend.relevance_score, 2) if trend.relevance_score else 0
            })
            
        return render_template('dashboard.html', 
                             trends=trends_data, 
                             topics=topics, 
                             current_topic=topic_filter,
                             current_category=category_filter)

@app.route('/click/<int:trend_id>')
def track_click(trend_id):
    """Log user activity and redirect to the real URL."""
    with get_db_session() as session:
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
