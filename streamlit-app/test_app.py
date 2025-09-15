"""
Test script to verify the application can start without errors
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_imports():
    """Test if all modules can be imported without errors"""
    try:
        print("Testing imports...")
        
        # Test main app
        from app import main
        print("✅ Main app imported successfully")
        
        # Test views
        from views import (
            render_dashboard,
            render_students_list, 
            render_registration, 
            render_attendance, 
        )
        print("✅ All views imported successfully")
        
        # Test components
        from components import ReadinessProcessor
        print("✅ Components imported successfully")
        
        # Test controllers
        from controllers.api_controller import APIController
        print("✅ API controller imported successfully")
        
        # Test utils
        from utils.config import AppConfig
        from utils.session_manager import SessionManager
        from utils.camera_utils import inject_camera_guides
        print("✅ All utils imported successfully")
        
        print("\n🎉 All imports successful! The application should run without errors.")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_basic_functionality():
    """Test basic functionality without running the full app"""
    try:
        print("\nTesting basic functionality...")
        
        # Test configuration
        from utils.config import AppConfig
        config = AppConfig()
        print("✅ Configuration loaded")
        
        # Test session manager
        from utils.session_manager import SessionManager
        session_manager = SessionManager()
        print("✅ Session manager initialized")
        
        # Test API controller
        from controllers.api_controller import APIController
        api_controller = APIController()
        print("✅ API controller initialized")
        
        print("🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Streamlit Application...")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test basic functionality
    functionality_ok = test_basic_functionality()
    
    print("\n" + "=" * 50)
    if imports_ok and functionality_ok:
        print("✅ All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("streamlit run app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
