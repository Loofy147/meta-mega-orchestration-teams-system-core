import os

def load_env(env_path=".env"):
    """
    Loads environment variables from a .env file.
    This is a simplified implementation of a dotenv loader.
    """
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle simple key=value or key=value_with_interpolation
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Simple interpolation for ${VAR}
                    if '$' in value:
                        for var_key, var_value in os.environ.items():
                            value = value.replace(f'${{{var_key}}}', var_value)
                        # Re-run interpolation for variables defined within the .env file itself
                        for var_key, var_value in os.environ.items():
                            value = value.replace(f'${{{var_key}}}', var_value)
                        
                    os.environ[key] = value
                    
    except FileNotFoundError:
        print(f"Warning: .env file not found at {env_path}. Using system environment variables.")
    except Exception as e:
        print(f"Error loading .env file: {e}")

if __name__ == "__main__":
    load_env()
    print("Environment variables loaded.")
