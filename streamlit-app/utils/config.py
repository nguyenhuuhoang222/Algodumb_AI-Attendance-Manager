import os
from typing import Dict, Any

class AppConfig:
    
    def __init__(self):
        self.faceid_service_url = os.getenv("FACEID_SERVICE_URL", "http://localhost:5000")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:5002")
        self.app_title = "AI Attendance Manager"
        # Removed app_icon as per instruction
        
    def get_css_styles(self) -> str:
        return """
        <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            --border-radius: 10px;
            --box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        h1 {
            color: var(--dark-color);
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-weight: 700;
        }
        
        h2 {
            color: var(--dark-color);
            margin-top: 30px;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        h3 {
            color: var(--dark-color);
            margin-top: 25px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .metric-card {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            padding: 25px;
            border-radius: var(--border-radius);
            color: white;
            text-align: center;
            box-shadow: var(--box-shadow);
            margin: 15px 0;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
        }
        
        .info-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: var(--border-radius);
            border-left: 4px solid var(--info-color);
            margin: 15px 0;
            box-shadow: var(--box-shadow);
        }
        
        .success-card {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            padding: 20px;
            border-radius: var(--border-radius);
            border-left: 4px solid var(--success-color);
            margin: 15px 0;
            box-shadow: var(--box-shadow);
        }
        
        .warning-card {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            padding: 20px;
            border-radius: var(--border-radius);
            border-left: 4px solid var(--warning-color);
            margin: 15px 0;
            box-shadow: var(--box-shadow);
        }
        
        .error-card {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            padding: 20px;
            border-radius: var(--border-radius);
            border-left: 4px solid var(--danger-color);
            margin: 15px 0;
            box-shadow: var(--box-shadow);
        }
        
        .stButton > button {
            border-radius: 20px;
            border: none;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: var(--box-shadow);
            margin: 0.25rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        
        .stButton {
            margin: 0.25rem;
        }
        
        .stForm .stButton {
            margin: 0.5rem 0;
        }
        
        .camera-controls {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: var(--border-radius);
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .status-indicator {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin: 0.25rem;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .status-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(45deg, var(--success-color), #45a049);
            color: white;
        }
        
        .stButton > button[kind="secondary"] {
            background: linear-gradient(45deg, #6c757d, #5a6268);
            color: white;
        }
        
        .dataframe {
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--box-shadow);
            border: 1px solid #e0e0e0;
        }
        
        .stAlert {
            border-radius: var(--border-radius);
            border: none;
            box-shadow: var(--box-shadow);
        }
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--success-color), #8BC34A);
            border-radius: var(--border-radius);
        }
        
        .webrtc-container {
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            margin: 20px 0;
            border: 2px solid #e0e0e0;
        }
        
        .status-present {
            color: var(--success-color);
            font-weight: bold;
        }
        
        .status-absent {
            color: var(--danger-color);
            font-weight: bold;
        }
        
        .status-partial {
            color: var(--warning-color);
            font-weight: bold;
        }
        
        
        .stForm {
            border: 1px solid #e0e0e0;
            border-radius: var(--border-radius);
            padding: 20px;
            background: white;
            box-shadow: var(--box-shadow);
        }
        
        .registration-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            color: white;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0 0 10px 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.1rem;
            margin: 0;
            opacity: 0.9;
        }
        
        .capture-instructions {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .instruction-header h4 {
            margin: 0 0 15px 0;
            color: #495057;
            font-weight: 600;
        }
        
        .instruction-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .instruction-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            font-size: 0.95rem;
            color: #6c757d;
        }
        
        /* Removed .instruction-icon as per instruction */
        
        .auto-camera-instructions {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border: 2px solid #2196f3;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(33, 150, 243, 0.2);
        }
        
        .auto-camera-instructions .instruction-header h4 {
            margin: 0 0 15px 0;
            color: #1565c0;
            font-weight: 600;
        }
        
        .form-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
        }
        
        .form-header h4 {
            margin: 0 0 8px 0;
            color: #495057;
            font-weight: 600;
        }
        
        .form-header p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .auto-generated-field {
            margin-bottom: 1rem;
        }
        
        .field-label {
            display: block;
            font-weight: 600;
            color: #495057;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        
        .field-value {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0.75rem;
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
            border: 2px solid #28a745;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(40, 167, 69, 0.1);
        }
        
        .student-id {
            font-family: 'Courier New', monospace;
            font-weight: 700;
            font-size: 1.1rem;
            color: #155724;
            letter-spacing: 0.5px;
        }
        
        .auto-badge {
            background: #28a745;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-ready {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
        }
        
        .status-processing {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 2px solid #ffc107;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            display: flex;
            align-items: flex-start;
            gap: 15px;
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);
        }
        
        /* Removed .status-icon as per instruction */
        
        .status-text h4 {
            margin: 0 0 8px 0;
            color: #495057;
            font-weight: 600;
        }
        
        .status-text p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        
        .capture-actions {
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
            border: 2px solid #28a745;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
        }
        
        .capture-actions h4 {
            margin: 0 0 8px 0;
            color: #155724;
            font-weight: 600;
        }
        
        .capture-actions p {
            margin: 0;
            color: #155724;
            font-size: 0.9rem;
        }
        
        .capture-success {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border: 2px solid #17a2b8;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(23, 162, 184, 0.2);
        }
        
        .capture-success h4 {
            margin: 0 0 8px 0;
            color: #0c5460;
            font-weight: 600;
        }
        
        .capture-success p {
            margin: 0;
            color: #0c5460;
            font-size: 0.9rem;
        }
        
        .camera-error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 2px solid #dc3545;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.2);
        }
        
        .camera-error h4 {
            margin: 0 0 8px 0;
            color: #721c24;
            font-weight: 600;
        }
        
        .camera-error p {
            margin: 0;
            color: #721c24;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
            }
            
            .metric-card {
                padding: 15px;
                margin: 10px 0;
            }
            
            .registration-header {
                padding: 20px 15px;
                margin-bottom: 20px;
            }
            
            .main-title {
                font-size: 1.8rem;
            }
            
            .subtitle {
                font-size: 1rem;
            }
            
            .form-container {
                padding: 15px;
            }
            
            .instruction-list {
                gap: 8px;
            }
            
            .instruction-item {
                font-size: 0.9rem;
                padding: 6px 0;
            }
            
            .status-ready,
            .status-processing {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            
            .capture-actions,
            .capture-success,
            .camera-error {
                padding: 15px;
                margin: 10px 0;
            }
            
            .webrtc-container {
                margin: 15px 0;
            }
        }
        
        @media (max-width: 480px) {
            .main .block-container {
                padding: 0.5rem;
            }
            
            .registration-header {
                padding: 15px 10px;
            }
            
            .main-title {
                font-size: 1.5rem;
            }
            
            .subtitle {
                font-size: 0.9rem;
            }
            
            .form-container {
                padding: 10px;
            }
            
            .instruction-item {
                font-size: 0.85rem;
            }
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """
    
    def get_theme_config(self) -> Dict[str, Any]:
        return {
            "primaryColor": "#667eea",
            "backgroundColor": "#ffffff",
            "secondaryBackgroundColor": "#f8f9fa",
            "textColor": "#262730",
            "font": "sans serif"
        }
