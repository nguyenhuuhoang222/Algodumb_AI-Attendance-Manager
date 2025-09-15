import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from controllers.api_controller import api_controller
from utils.session_manager import SessionManager

def render_dashboard():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2c3e50; margin-bottom: 10px;">Dashboard</h1>
        <p style="color: #7f8c8d; font-size: 16px;">AI Attendance System Overview</p>
    </div>
    """, unsafe_allow_html=True)
    
    dashboard_data = get_dashboard_data()
    
    render_metrics_cards(dashboard_data)
    
    render_attendance_list_by_date(dashboard_data)
    
    render_quick_actions()

def get_dashboard_data():
    try:
        data = api_controller.get_dashboard_data()
        if not isinstance(data, dict):
            data = {}
        
        return {
            "total_students": data.get("total_students", 0),
            "present_today": data.get("present_today", 0),
            "attendance_rate": data.get("attendance_rate", 0),
            "students": data.get("students", []),
            "attendance": data.get("attendance", []),
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d"))
        }
    except Exception as e:
        st.error(f"Failed to load dashboard data: {str(e)}")
        return {
            "total_students": 0,
            "present_today": 0,
            "attendance_rate": 0,
            "students": [],
            "attendance": [],
            "date": datetime.now().strftime("%Y-%m-%d")
        }

def render_metrics_cards(data):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 28px;">{data['total_students']}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Total Students</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 28px;">{data['present_today']}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Present Today</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        attendance_rate = data['attendance_rate']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 28px;">{attendance_rate:.1f}%</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Attendance Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        today = datetime.now().strftime("%A")
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin: 0; font-size: 28px;">{today}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Today</p>
        </div>
        """, unsafe_allow_html=True)

def render_attendance_list_by_date(data):
    st.markdown("### Attendance Records by Date")
    
    if not data['attendance']:
        st.info("No attendance records found")
        return
    
    attendance_by_date = {}
    for att in data['attendance']:
        timestamp = att.get('timestamp', '')
        if timestamp:
            try:
                if 'T' in timestamp:
                    date_str = timestamp.split('T')[0]
                else:
                    date_str = timestamp.split(' ')[0]
                
                if date_str not in attendance_by_date:
                    attendance_by_date[date_str] = []
                
                attendance_by_date[date_str].append(att)
            except:
                continue
    
    for date_str in attendance_by_date:
        attendance_by_date[date_str].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    sorted_dates = sorted(attendance_by_date.keys(), reverse=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    st.markdown("**Select Date to View:**")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        available_dates = []
        for date_str in sorted_dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                available_dates.append(date_obj)
            except:
                continue
        
        default_date = datetime.now().date()
        if available_dates:
            if today in attendance_by_date:
                default_date = datetime.now().date()
            else:
                default_date = available_dates[0]
        
        selected_date = st.date_input(
            "Choose a date:",
            value=default_date,
            key="attendance_date_picker",
            help="Select a date to view attendance records"
        )
        
        selected_date_str = selected_date.strftime("%Y-%m-%d")
    
    with col2:
        if st.button("Today", use_container_width=True, key="today_btn"):
            st.session_state.attendance_selected_date = today
            st.rerun()
    
    with col3:
        if st.button("Yesterday", use_container_width=True, key="yesterday_btn"):
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            st.session_state.attendance_selected_date = yesterday
            st.rerun()
    
    with col4:
        if st.button("Refresh", use_container_width=True, type="primary", key="refresh_btn"):
            st.rerun()
    
    if 'attendance_selected_date' in st.session_state:
        selected_date_str = st.session_state.attendance_selected_date
        del st.session_state.attendance_selected_date
    
    st.markdown(f"**Selected Date: {selected_date_str}**")
    
    date_attendance = attendance_by_date.get(selected_date_str, [])
    attendance_dict = {att.get('student_id'): att for att in date_attendance}
    
    
    if selected_date_str in attendance_by_date:
        st.success(f"Found {len(date_attendance)} attendance records for {selected_date_str}")
    else:
        st.warning(f"No attendance records found for {selected_date_str}")
    
    attendance_list = []
    
    student_dict = {s.get('student_id'): s for s in data['students']}
    
    for student_id, student in student_dict.items():
        if student_id in attendance_dict:
            att = attendance_dict[student_id]
            
            
            att_type = att.get('type', '')
            if att_type == 'checkin':
                att_status = 'Check In'
            elif att_type == 'checkout':
                att_status = 'Present'
            elif att_type == 'attendance':
                att_status = 'Present'
            else:
                att_status = 'Present'
            
            att_time = att.get('timestamp', '')
            if 'T' in att_time:
                time_str = att_time.split('T')[1][:8]
            else:
                time_str = att_time.split(' ')[1][:8] if ' ' in att_time else att_time
        else:
            att_status = 'Absent'
            time_str = '-'
        
        attendance_list.append({
            'Student ID': student_id,
            'Name': student.get('full_name', 'Unknown'),
            'Class': student.get('class_name', 'Unknown'),
            'Action': att_status,
            'Time': time_str,
            'Timestamp': att.get('timestamp', '') if student_id in attendance_dict else ''
        })
    
    if attendance_list:
        def sort_key(x):
            status_priority = 0 if x['Action'] in ['Check In', 'Present'] else 1
            if x['Action'] in ['Check In', 'Present'] and x['Timestamp']:
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(x['Timestamp'].replace('Z', '+00:00'))
                    return (status_priority, timestamp)
                except:
                    return (status_priority, x['Name'])
            else:
                return (status_priority, x['Name'])
        
        attendance_list.sort(key=sort_key)
        
        present_count = len([s for s in attendance_list if s['Action'] in ['Check In', 'Present']])
        absent_count = len([s for s in attendance_list if s['Action'] == 'Absent'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"Present: {present_count}")
        with col2:
            st.error(f"Absent: {absent_count}")
        with col3:
            st.info(f"Total: {len(attendance_list)}")
        
        st.markdown(f"**Student Attendance List for {selected_date_str}:**")
        
        df = pd.DataFrame(attendance_list)
        st.dataframe(
            df, 
            use_container_width=True, 
            height=400,
            column_config={
                "Student ID": st.column_config.TextColumn("Student ID", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Class": st.column_config.TextColumn("Class", width="small"),
                "Action": st.column_config.TextColumn("Status", width="small"),
                "Time": st.column_config.TextColumn("Time", width="small")
            }
        )
    else:
        st.info(f"No students found for {selected_date_str}")

def render_students_list(data):
    st.markdown("### Attendance Records by Date")
    
    if not data['students']:
        st.info("No students registered yet")
        return
    
    attendance_by_date = {}
    for att in data['attendance']:
        timestamp = att.get('timestamp', '')
        if timestamp:
            try:
                if 'T' in timestamp:
                    date_str = timestamp.split('T')[0]
                else:
                    date_str = timestamp.split(' ')[0]
                
                if date_str not in attendance_by_date:
                    attendance_by_date[date_str] = []
                
                attendance_by_date[date_str].append(att)
            except:
                continue
    
    for date_str in attendance_by_date:
        attendance_by_date[date_str].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not attendance_by_date:
        attendance_by_date = {today: []}
    
    sorted_dates = sorted(attendance_by_date.keys(), reverse=True)
    
    st.markdown("**Select Date to View:**")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        available_dates = []
        for date_str in sorted_dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                available_dates.append(date_obj)
            except:
                continue
        
        selected_date = st.date_input(
            "Choose a date:",
            value=datetime.now().date(),
            key="students_date_picker",
            label_visibility="collapsed",
            help="Click to select a date"
        )
        
        selected_date_str = selected_date.strftime("%Y-%m-%d")
    
    with col2:
        if st.button("Today", key="today_students_btn"):
            st.rerun()
    
    with col3:
        if st.button("Yesterday", key="yesterday_students_btn"):
            st.rerun()
    
    with col4:
        if st.button("Refresh", key="refresh_btn", type="primary"):
            st.rerun()
    
    st.markdown(f"**Selected Date: {selected_date_str}**")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    st.caption(f"Debug: selected_date_str={selected_date_str}, today_str={today_str}")
    st.caption(f"Available dates: {sorted_dates[:5] if sorted_dates else 'None'}")
    
    st.success(f"Viewing attendance for {selected_date_str}")
    
    date_attendance = attendance_by_date.get(selected_date_str, [])
    attendance_dict = {att.get('student_id'): att for att in date_attendance}
    
    if selected_date_str in attendance_by_date:
        st.info(f"Found {len(date_attendance)} attendance records for {selected_date_str}")
    else:
        st.warning(f"No attendance records found for {selected_date_str}")
    
    attendance_list = []
    
    for student in data['students']:
        student_id = student.get('student_id', 'Unknown')
        
        if student_id in attendance_dict:
            att = attendance_dict[student_id]
            
            att_type = att.get('type', '')
            if att_type == 'checkin':
                att_status = 'Check In'
            elif att_type == 'checkout':
                att_status = 'Present'
            elif att_type == 'attendance':
                att_status = 'Present'
            else:
                att_status = 'Present'
            
            att_time = att.get('timestamp', '')
            if 'T' in att_time:
                time_str = att_time.split('T')[1][:8]
            else:
                time_str = att_time.split(' ')[1][:8] if ' ' in att_time else att_time
        else:
            att_status = 'Absent'
            time_str = '-'
        
        attendance_list.append({
            'Student ID': student_id,
            'Name': student.get('full_name', 'Unknown'),
            'Class': student.get('class_name', 'Unknown'),
            'Action': att_status,
            'Time': time_str,
            'Timestamp': att.get('timestamp', '') if student_id in attendance_dict else ''
        })
    
    if attendance_list:
        def sort_key(x):
            status_priority = 0 if x['Action'] in ['Check In', 'Present'] else 1
            if x['Action'] in ['Check In', 'Present'] and x['Timestamp']:
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(x['Timestamp'].replace('Z', '+00:00'))
                    return (status_priority, timestamp)
                except:
                    return (status_priority, x['Name'])
            else:
                return (status_priority, x['Name'])
        
        attendance_list.sort(key=sort_key)
        
        present_count = len([s for s in attendance_list if s['Action'] in ['Check In', 'Present']])
        absent_count = len([s for s in attendance_list if s['Action'] == 'Absent'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"Present: {present_count}")
        with col2:
            st.error(f"Absent: {absent_count}")
        with col3:
            st.info(f"Total: {len(attendance_list)}")
        
        st.markdown(f"**Student Attendance List for {selected_date_str}:**")
        
        df = pd.DataFrame(attendance_list)
        st.dataframe(
            df, 
            use_container_width=True, 
            height=400,
            column_config={
                "Student ID": st.column_config.TextColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Class": st.column_config.TextColumn("Class", width="small"),
                "Action": st.column_config.TextColumn("Action", width="medium"),
                "Time": st.column_config.TextColumn("Time", width="small")
            }
        )
    else:
        st.info(f"No students found for {selected_date_str}")
    
    st.markdown("**Quick Navigation - Click to select date:**")
    
    display_dates = sorted_dates[:5]
    if display_dates:
        nav_cols = st.columns(len(display_dates))
        
        for i, date in enumerate(display_dates):
            with nav_cols[i]:
                is_selected = date == selected_date_str
                if is_selected:
                    st.button(f"{date}", key=f"nav_{date}", disabled=True, help="Currently selected")
                else:
                    if st.button(f"{date}", key=f"nav_{date}", help=f"Click to view attendance for {date}"):
                        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
                        selected_date_str = date
                        st.session_state.confirmed_date = selected_date_str
                        st.rerun()
        
        if len(sorted_dates) > 5:
            st.caption(f"Showing last 5 dates. Total available: {len(sorted_dates)} dates")
    else:
        st.info("No attendance dates available")

def render_quick_actions():
    st.markdown("### Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Take Attendance", use_container_width=True):
            st.session_state.current_page = 'attendance'
            st.rerun()
    
    with col2:
        if st.button("Register Student", use_container_width=True):
            st.session_state.current_page = 'registration'
            st.rerun()
    
    with col3:
        if st.button("Download Report", use_container_width=True):
            generate_download_report()
    
    if st.button("Refresh Data", use_container_width=True):
        st.rerun()

def generate_download_report():
    try:
        data = get_dashboard_data()
        
        report_data = []
        for student in data['students']:
            student_id = student.get('student_id', '')
            name = student.get('full_name', 'Unknown')
            class_name = student.get('class_name', 'Unknown')
            
            attendance_status = "Absent"
            attendance_time = "-"
            
            for att in data['attendance']:
                if att.get('student_id') == student_id:
                    att_type = att.get('type', '')
                    if att_type == 'checkin':
                        attendance_status = 'Check In'
                    elif att_type == 'checkout':
                        attendance_status = 'Present'
                    elif att_type == 'attendance':
                        attendance_status = 'Present'
                    else:
                        attendance_status = 'Present'
                    
                    att_time = att.get('timestamp', '')
                    if 'T' in att_time:
                        attendance_time = att_time.split('T')[1][:8]
                    else:
                        attendance_time = att_time.split(' ')[1][:8] if ' ' in att_time else att_time
                    break
            
            report_data.append({
                'Student ID': student_id,
                'Name': name,
                'Class': class_name,
                'Status': attendance_status,
                'Time': attendance_time
            })
        
        df = pd.DataFrame(report_data)
        
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name=f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.success("Report generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
