import subprocess
import json

def run_lighthouse(url: str) -> float:
    try:
        # Run lighthouse CLI
        result = subprocess.run([
            "lighthouse",
            url,
            "--output=json",
            "--quiet"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("categories", {}).get("performance", {}).get("score", 0) * 100
        else:
            raise Exception(f"Lighthouse failed: {result.stderr}")
    except Exception as e:
        print(f"Error running lighthouse: {str(e)}")
        return 0.0
