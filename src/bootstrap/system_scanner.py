from src.bootstrap.tool_scanner import scan_tools
from src.bootstrap.project_analyzer import analyze_project as analyze_project_file
from src.bootstrap.platform_scanner import scan_platforms
from src.bootstrap.credential_scanner import scan_credentials, get_credential_status
from src.bootstrap.dedup_registry import register_dedup
from src.bootstrap.system_profile import HostingSystemProfile, set_profile, get_profile


def scan_system() -> HostingSystemProfile:
    """
    Complete system scan and profile generation.
    
    This is the HARD REQUIREMENT bootstrap phase that must complete
    before any agents activate. Follows the pattern from the original
    FPGA prompt's system scan bootstrap.
    
    Phases:
    1. EDA Toolchain Scan (development tools)
    2. Platform Scan (hosting platforms)
    3. Credential Scan (authentication)
    4. Dedup Registry (avoid redundant scans)
    5. Profile Write (FPGASystemProfile pattern)
    """
    print("=" * 50)
    print("OPEN.HOST JARVIS - SYSTEM BOOTSTRAP")
    print("=" * 50)
    
    # Phase 1: Tool Detection
    print("\n[Phase 1] Scanning development tools...")
    tools = scan_tools()
    tool_count = sum(1 for v in tools.values() if v is not None)
    print(f"  -> {tool_count} tools detected")
    for tool, version in tools.items():
        status = "[OK]" if version else "[--]"
        print(f"    {status} {tool}: {version or 'not found'}")

    # Phase 2: Platform Scan
    print("\n[Phase 2] Scanning hosting platforms...")
    platforms = scan_platforms()
    print(f"  -> {len(platforms)} platforms available")
    for platform in platforms:
        health = "[OK]" if platform.get("healthy") else "[--]"
        print(f"    {health} {platform['name']}: {platform.get('display_name', platform['name'])}")

    # Phase 3: Credential Scan
    print("\n[Phase 3] Scanning credentials...")
    credentials = scan_credentials()
    cred_status = get_credential_status()
    print(f"  -> {len(credentials)} credentials found")
    for platform, status in cred_status.items():
        valid = "[OK]" if status.get("valid") else "[--]"
        print(f"    {valid} {platform}: {status.get('masked', '***')}")

    # Phase 4: Project Analysis (default)
    print("\n[Phase 4] Analyzing default project type...")
    try:
        # Try to analyze current directory as a project
        project_info = analyze_project_file(".")
        project_type = project_info.get("project_type", "unknown")
        print(f"  -> Project type: {project_type}")
    except Exception as e:
        project_type = None
        print(f"  -> No project detected in current directory")

    # Phase 5: Dedup Registry
    print("\n[Phase 5] Registering dedup entries...")
    register_dedup(tools, platforms, {"project_type": project_type})
    print("  -> Dedup registry updated")

    # Phase 6: Build System Profile
    print("\n[Phase 6] Building system profile...")
    profile = HostingSystemProfile(
        tools={k: v for k, v in tools.items() if v is not None},
        project_type=project_type,
        build_settings={},
        platforms=platforms,
        credentials=credentials,
        inference_config=_detect_inference_config(),
        capabilities=_calculate_capabilities(tools, platforms, credentials)
    )

    # Set global profile
    set_profile(profile)

    # Save to file
    profile.save_to_file()
    print(f"  -> Profile saved to system_profile.json")

    # Validation
    print("\n" + "=" * 50)
    if profile.is_validated():
        print("SYSTEM BOOTSTRAP: VALIDATED [OK]")
    else:
        print("SYSTEM BOOTSTRAP: NOT VALIDATED [--]")
        print("  Warning: Some requirements not met. Agents may have limited functionality.")
    print("=" * 50)
    
    return profile


def _detect_inference_config() -> dict:
    """Detect LLM inference server configuration."""
    config = {
        "available": False,
        "servers": []
    }
    
    # Check for common inference server ports
    import httpx
    
    ports = [11434, 8000, 8080, 5000]  # ollama, fastapi, etc.
    
    for port in ports:
        try:
            response = httpx.get(f"http://localhost:{port}", timeout=2)
            if response.status_code < 500:
                config["servers"].append({
                    "port": port,
                    "healthy": True
                })
                config["available"] = True
        except Exception:
            continue
    
    return config


def _calculate_capabilities(tools: dict, platforms: list, credentials: dict) -> dict:
    """Calculate system capabilities based on detected tools and platforms."""
    return {
        "node_deploy": tools.get("node") is not None and tools.get("npm") is not None,
        "python_deploy": tools.get("python3") is not None,
        "docker_deploy": tools.get("docker") is not None,
        "netlify_deploy": (credentials.get("netlify") is not None or 
                          tools.get("netlify") is not None),
        "vercel_deploy": (credentials.get("vercel") is not None or 
                         tools.get("vercel") is not None),
        "github_pages_deploy": (credentials.get("github") is not None or 
                               tools.get("gh") is not None),
        "render_deploy": (credentials.get("render") is not None or 
                         tools.get("render") is not None),
        "llm_inference": False,  # Would be set by _detect_inference_config
    }


# Convenience function for project analysis
def analyze_project(project_path: str) -> dict:
    """Analyze a project at the given path."""
    return analyze_project_file(project_path)
