from src.bootstrap.tool_scanner import scan_tools
from src.bootstrap.project_analyzer import analyze_project
from src.bootstrap.platform_scanner import scan_platforms
from src.bootstrap.credential_scanner import scan_credentials
from src.bootstrap.dedup_registry import register_dedup
from src.bootstrap.system_profile import HostingSystemProfile

def scan_system():
    print("Starting system scan...")
    tools = scan_tools()
    project_type, build_settings = analyze_project()
    platforms = scan_platforms()
    credentials = scan_credentials()
    register_dedup(tools, platforms, project_type)
    
    HostingSystemProfile.tools = tools
    HostingSystemProfile.project_type = project_type
    HostingSystemProfile.build_settings = build_settings
    HostingSystemProfile.platforms = platforms
    HostingSystemProfile.credentials = credentials
    
    print("System scan complete.")
