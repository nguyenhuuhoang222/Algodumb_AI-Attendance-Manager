"""
Views package - UI view components
"""
from .dashboard_view import render_dashboard
from .registration_view import render_registration
from .attendance_view import render_attendance

__all__ = [
    'render_dashboard',
    'render_registration', 
    'render_attendance'
]