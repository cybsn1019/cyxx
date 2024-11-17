import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go


# Page configuration
st.set_page_config(
    page_title="Cyber Cafe Management",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with neon colors and modern design
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .custom-div {
        background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #00ff9d;
        color: #00ff9d;
        box-shadow: 0 0 15px rgba(0, 255, 157, 0.2);
    }
    .custom-div h4 {
        color: #00ffff;
        text-shadow: 0 0 5px #00ffff;
    }
    .custom-div p {
        color: #f0f0f0;
    }
    .stButton button {
        width: 100%;
        background: linear-gradient(45deg, #00ff9d, #00ffff);
        color: #1a1a1a;
        border: none;
        font-weight: bold;
    }
    .status-card {
        background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.15);
        color: #00ff9d;
    }
    .status-card h3 {
        color: #00ffff;
        text-shadow: 0 0 5px #00ffff;
    }
    .status-card p {
        color: #f0f0f0;
        margin: 0.5rem 0;
    }
    .metric-card {
        background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.15);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card h3 {
        color: #00ffff;
        text-shadow: 0 0 5px #00ffff;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .metric-card h2 {
        color: #00ff9d;
        text-shadow: 0 0 5px #00ff9d;
        font-size: 2rem;
        margin: 0;
    }
    /* Override Streamlit's default white background */
    .stApp {
        background: linear-gradient(to bottom right, #0a0a0a, #1a1a1a);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #1a1a1a;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2a2a2a;
        color: #00ff9d;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ff9d !important;
        color: #1a1a1a !important;
    }
    /* Form styling */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #2a2a2a;
        color: #00ff9d;
        border: 1px solid #00ff9d;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: #00ffff;
        box-shadow: 0 0 5px #00ffff;
    }
    /* Plotly chart background */
    .js-plotly-plot .plotly {
        background-color: #1a1a1a !important;
    }
    .js-plotly-plot .bg {
        fill: #1a1a1a !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize the database
def init_db():
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create computers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            specifications TEXT,
            last_maintenance TIMESTAMP,
            hourly_rate REAL DEFAULT 30.0
        )
    ''')

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            computer_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            duration INTEGER,
            cost REAL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (computer_id) REFERENCES computers (id)
        )
    ''')

    # Create maintenance_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_id INTEGER,
            maintenance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            technician TEXT,
            FOREIGN KEY (computer_id) REFERENCES computers (id)
        )
    ''')

    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            price_per_item REAL,
            category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert sample computers if none exist
    cursor.execute('SELECT COUNT(*) FROM computers')
    if cursor.fetchone()[0] == 0:
        sample_computers = [
            ('PC-01', 'available', 'Intel i5, 16GB RAM, RTX 3060', datetime.now(), 30.0),
            ('PC-02', 'available', 'Intel i7, 32GB RAM, RTX 3070', datetime.now(), 35.0),
            ('PC-03', 'available', 'AMD Ryzen 7, 16GB RAM, RX 6700', datetime.now(), 30.0)
        ]
        cursor.executemany('''
            INSERT INTO computers (name, status, specifications, last_maintenance, hourly_rate)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_computers)

    conn.commit()
    conn.close()

# Authentication functions
def register_user():
    st.subheader("📝 Register New User")
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email")
        with col2:
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords do not match!")
                return
            
            conn = sqlite3.connect('cyber_cafe.db')
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                             (name, email, password))
                conn.commit()
                st.success("Registration successful! Please login.")
            except sqlite3.IntegrityError:
                st.error("Email already exists!")
            finally:
                conn.close()

def login_user():
    st.subheader("🔐 User Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            conn = sqlite3.connect('cyber_cafe.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                         (email, password))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state['user'] = {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'role': user[4]
                }
                st.success(f"Welcome back, {user[1]}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials!")

# Session management functions
def start_session():
    st.subheader("🎮 Start New Session")
    
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    # Get available computers
    cursor.execute('SELECT id, name, specifications, hourly_rate FROM computers WHERE status = "available"')
    available_computers = cursor.fetchall()
    
    if not available_computers:
        st.warning("No computers available at the moment.")
        conn.close()
        return
    
    with st.form("start_session_form"):
        # Create a more detailed computer selection
        computer_options = {f"{pc[1]} (₹{pc[3]}/hr) - {pc[2]}": pc[0] for pc in available_computers}
        selected_computer = st.selectbox(
            "Select Computer",
            options=list(computer_options.keys())
        )
        
        hours = st.number_input("Estimated Hours", min_value=0.5, max_value=12.0, value=1.0, step=0.5)
        
        col1, col2 = st.columns(2)
        with col1:
            start_button = st.form_submit_button("Start Session")
        with col2:
            estimated_cost = hours * next(pc[3] for pc in available_computers if pc[0] == computer_options[selected_computer])
            st.write(f"Estimated Cost: ₹{estimated_cost:.2f}")
        
        if start_button:
            computer_id = computer_options[selected_computer]
            user_id = st.session_state['user']['id']
            
            try:
                # Start new session
                cursor.execute('''
                    INSERT INTO sessions (user_id, computer_id, start_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, computer_id))
                
                # Update computer status
                cursor.execute('UPDATE computers SET status = "in-use" WHERE id = ?',
                             (computer_id,))
                
                conn.commit()
                st.success("Session started successfully!")
                
                # Show session details
                st.info(f"""
                    Session Details:
                    - Computer: {selected_computer.split(' (')[0]}
                    - Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    - Estimated Duration: {hours} hours
                    - Estimated Cost: ₹{estimated_cost:.2f}
                """)
                
            except sqlite3.Error as e:
                st.error(f"Error starting session: {e}")
    
    conn.close()

def end_session():
    st.subheader("⏹️ End Active Session")
    
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    # Get active sessions for the current user
    cursor.execute('''
        SELECT 
            s.id,
            c.name,
            s.start_time,
            c.hourly_rate
        FROM sessions s
        JOIN computers c ON s.computer_id = c.id
        WHERE s.user_id = ? AND s.end_time IS NULL
    ''', (st.session_state['user']['id'],))
    
    active_sessions = cursor.fetchall()
    
    if not active_sessions:
        st.info("No active sessions found.")
        conn.close()
        return
    
    for session in active_sessions:
        session_id, computer_name, start_time, hourly_rate = session
        start_time = datetime.fromisoformat(start_time)
        duration = (datetime.now() - start_time).total_seconds() / 3600  # hours
        cost = duration * hourly_rate
        
        st.markdown(f"""
            <div class="custom-div">
                <h4>{computer_name}</h4>
                <p>Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Duration: {duration:.2f} hours</p>
                <p>Cost: ₹{cost:.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"End Session {session_id}"):
            try:
                # Update session
                cursor.execute('''
                    UPDATE sessions 
                    SET end_time = CURRENT_TIMESTAMP,
                        duration = ?,
                        cost = ?
                    WHERE id = ?
                ''', (duration, cost, session_id))
                
                # Update computer status
                cursor.execute('''
                    UPDATE computers 
                    SET status = "available" 
                    WHERE id = (
                        SELECT computer_id 
                        FROM sessions 
                        WHERE id = ?
                    )
                ''', (session_id,))
                
                conn.commit()
                st.success(f"""
                    Session ended successfully!
                    Final Duration: {duration:.2f} hours
                    Total Cost: ₹{cost:.2f}
                """)
                st.experimental_rerun()
                
            except sqlite3.Error as e:
                st.error(f"Error ending session: {e}")
    
    conn.close()

# Computer management functions
def show_computer_status():
    st.subheader("💻 Computer Status")
    
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    # Get all computers with their current status
    cursor.execute('''
        SELECT 
            c.id,
            c.name,
            c.status,
            c.specifications,
            c.last_maintenance,
            CASE 
                WHEN s.id IS NOT NULL THEN u.name 
                ELSE NULL 
            END as current_user,
            s.start_time
        FROM computers c
        LEFT JOIN sessions s ON c.id = s.computer_id AND s.end_time IS NULL
        LEFT JOIN users u ON s.user_id = u.id
    ''')
    computers = cursor.fetchall()
    
    # Display computers in a grid
    cols = st.columns(3)
    for idx, computer in enumerate(computers):
        with cols[idx % 3]:
            status_color = {
                'available': 'green',
                'in-use': 'orange',
                'maintenance': 'red'
            }.get(computer[2], 'grey')
            
            st.markdown(f"""
                <div class="status-card" style="border-left: 5px solid {status_color}">
                    <h3>{computer[1]}</h3>
                    <p><strong>Status:</strong> {computer[2].title()}</p>
                    <p><strong>Specs:</strong> {computer[3]}</p>
                    <p><strong>Last Maintenance:</strong> {computer[4]}</p>
                    {f'<p><strong>Current User:</strong> {computer[5]}</p>' if computer[5] else ''}
                    {f'<p><strong>Session Start:</strong> {computer[6]}</p>' if computer[6] else ''}
                </div>
            """, unsafe_allow_html=True)
            
            if computer[2] != 'maintenance':
                if st.button(f"Schedule Maintenance {computer[0]}", key=f"maint_{computer[0]}"):
                    st.session_state['maintenance_computer_id'] = computer[0]
                    st.session_state['show_maintenance_form'] = True
    
    conn.close()

def manage_maintenance():
    st.subheader("🔧 Maintenance Management")
    
    if 'show_maintenance_form' in st.session_state and st.session_state['show_maintenance_form']:
        schedule_maintenance(st.session_state['maintenance_computer_id'])
    else:
        show_maintenance_history()

def schedule_maintenance(computer_id):
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    # Get computer details
    cursor.execute('SELECT name, specifications FROM computers WHERE id = ?', (computer_id,))
    computer = cursor.fetchone()
    
    st.markdown(f"""
        <div class="custom-div">
            <h3>Schedule Maintenance for {computer[0]}</h3>
            <p>{computer[1]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("maintenance_form"):
        maintenance_type = st.selectbox(
            "Maintenance Type",
            ["Routine Checkup", "Hardware Repair", "Software Update", "Deep Cleaning", "Other"]
        )
        
        description = st.text_area("Description", placeholder="Describe the maintenance work...")
        technician = st.text_input("Technician Name")
        
        col1, col2 = st.columns(2)
        with col1:
            estimated_duration = st.number_input(
                "Estimated Duration (hours)",
                min_value=0.5,
                max_value=72.0,
                value=1.0,
                step=0.5
            )
        with col2:
            priority = st.select_slider(
                "Priority",
                options=["Low", "Medium", "High", "Critical"]
            )
        
        if st.form_submit_button("Schedule"):
            try:
                # Add maintenance log
                cursor.execute('''
                    INSERT INTO maintenance_logs 
                    (computer_id, description, technician)
                    VALUES (?, ?, ?)
                ''', (computer_id, f"{maintenance_type}: {description}", technician))
                
                # Update computer status
                cursor.execute('''
                    UPDATE computers 
                    SET status = 'maintenance',
                        last_maintenance = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (computer_id,))
                
                conn.commit()
                st.success("Maintenance scheduled successfully!")
                st.session_state['show_maintenance_form'] = False
                st.experimental_rerun()
                
            except sqlite3.Error as e:
                st.error(f"Error scheduling maintenance: {e}")
    
    conn.close()

def show_maintenance_history():
    st.subheader("Maintenance History")
    
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.name,
            m.maintenance_date,
            m.description,
            m.technician
        FROM maintenance_logs m
        JOIN computers c ON m.computer_id = c.id
        ORDER BY m.maintenance_date DESC
        LIMIT 10
    ''')
    
    maintenance_history = cursor.fetchall()
    
    if maintenance_history:
        for record in maintenance_history:
            st.markdown(f"""
                <div class="custom-div">
                    <h4>{record[0]}</h4>
                    <p>📅 {record[1]}</p>
                    <p>👨‍🔧 {record[3]}</p>
                    <p>{record[2]}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No maintenance history available")
    
    conn.close()

# Dashboard functions
def show_dashboard():
    st.subheader("📊 Dashboard")
    
    conn = sqlite3.connect('cyber_cafe.db')
    cursor = conn.cursor()
    
    # Get key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE DATE(start_time) = DATE("now")')
        today_sessions = cursor.fetchone()[0]
        st.markdown(f"""
            <div class="metric-card">
                <h3>Today's Sessions</h3>
                <h2>{today_sessions}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cursor.execute('SELECT COUNT(*) FROM computers WHERE status = "available"')
        available_computers = cursor.fetchone()[0]
        st.markdown(f"""
            <div class="metric-card">
                <h3>Available Computers</h3>
                <h2>{available_computers}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cursor.execute('SELECT COUNT(*) FROM computers WHERE status = "maintenance"')
        maintenance_count = cursor.fetchone()[0]
        st.markdown(f"""
            <div class="metric-card">
                <h3>In Maintenance</h3>
                <h2>{maintenance_count}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        cursor.execute('SELECT SUM(cost) FROM sessions WHERE DATE(start_time) = DATE("now")')
        today_revenue = cursor.fetchone()[0] or 0
        st.markdown(f"""
            <div class="metric-card">
                <h3>Today's Revenue</h3>
                <h2>₹{today_revenue:.2f}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    # Usage trends
    st.subheader("Usage Trends")
    cursor.execute('''
        SELECT 
            DATE(start_time) as date,
            COUNT(*) as session_count,
            SUM(cost) as daily_revenue
        FROM sessions
        WHERE start_time >= DATE('now', '-30 days')
        GROUP BY DATE(start_time)
        ORDER BY date
    ''')
    usage_data = cursor.fetchall()
    
    if usage_data:
        df = pd.DataFrame(usage_data, columns=['date', 'session_count', 'daily_revenue'])
        
        tab1, tab2 = st.tabs(["Sessions", "Revenue"])
        
        with tab1:
            fig = px.line(df, x='date', y='session_count', title='Daily Sessions')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.line(df, x='date', y='daily_revenue', title='Daily Revenue')
            st.plotly_chart(fig, use_container_width=True)
    
    # Computer usage distribution
    st.subheader("Computer Usage Distribution")
    cursor.execute('''
        SELECT 
            c.name,
            COUNT(s.id) as session_count
        FROM computers c
        LEFT JOIN sessions s ON c.id = s.computer_id
        GROUP BY c.id, c.name
    ''')
    usage_dist = cursor.fetchall()
    
    if usage_dist:
        fig = go.Figure(data=[
            go.Bar(
                x=[u[0] for u in usage_dist],
                y=[u[1] for u in usage_dist]
            )
        ])
        fig.update_layout(title='Sessions per Computer')
        st.plotly_chart(fig, use_container_width=True)
    
    conn.close()

# Initialize database
init_db()

# Main menu
if 'user' not in st.session_state:
    selected = option_menu(
        menu_title=None,
        options=["Login", "Register"],
        icons=["box-arrow-in-right", "person-plus"],
        orientation="horizontal"
    )
    
    if selected == "Login":
        login_user()
    else:
        register_user()
else:
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Start Session", "End Session", "Computers", "Maintenance", "Logout"],
        icons=["graph-up", "play-circle", "stop-circle", "pc-display", "tools", "box-arrow-right"],
        orientation="horizontal"
    )
    
    if selected == "Dashboard":
        show_dashboard()
    elif selected == "Start Session":
        start_session()
    elif selected == "End Session":
        end_session()
    elif selected == "Computers":
        show_computer_status()
    elif selected == "Maintenance":
        manage_maintenance()
    elif selected == "Logout":
        st.session_state.clear()
        st.experimental_rerun()