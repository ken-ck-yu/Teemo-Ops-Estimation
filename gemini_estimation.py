import json
import time
import threading
import traceback
from google import genai
from pydantic import BaseModel

# Import flexible I/O functions
from file_reader import read_file_content
from file_writer import write_file_content


class Output(BaseModel):
    """Schema for ML training resource estimation output"""
    # Model Summary
    architecture: str
    parameters: str
    layers: str
    
    # Resource Requirements
    recommended_gpu: str
    vram_required: str
    cpu_cores: str
    ram: str
    
    # Training Time
    estimated_duration: str
    
    # Cost Estimate
    estimated_cost_usd: str
    cloud_provider: str
    
    # Energy Consumption
    estimated_kwh: str
    carbon_emission_kg: str
    
    # Other
    optimization_recommendations: list[str]
    confidence_level: str


def progress_counter(stop_event):
    """Display progress updates while waiting for Gemini response"""
    seconds = 0
    while not stop_event.is_set():
        time.sleep(5)
        seconds += 5
        if not stop_event.is_set():
            print(f"Still waiting... ({seconds}s elapsed)")


def run_estimation(provider=None, params_content=None, output_path=None, debug=False, 
                   api_key=None, model=None, system_prompt_path=None, user_prompt_template_path=None):
    """Run the resource estimation process with Gemini.
    
    Args:
        provider: AI provider (must be 'gemini')
        params_content: The extracted parameters as a string (file content)
        output_path: Path to save the estimation results
        debug: Enable debug mode
        api_key: Gemini API key
        model: Gemini model name
        system_prompt_path: Path to system prompt file
        user_prompt_template_path: Path to user prompt template file
    
    Returns:
        bool: True if successful, False otherwise
    """
    if provider != 'gemini':
        print(f"Error: Only 'gemini' provider is supported, got: {provider}")
        return False
    
    if not api_key:
        print("Error: Missing API key for Gemini")
        return False
    
    if not params_content:
        print("Error: Missing params_content")
        return False
    
    if not output_path:
        print("Error: Missing output_path")
        return False

    print(f"Starting estimation with Gemini...")
    print(f"  Model: {model}")
    print(f"  Script content length: {len(params_content)} characters")
    print(f"  Output path: {output_path}")
    print(f"  Debug mode: {debug}")

    try:
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        print("✓ Gemini client initialized")
        
        # Load system prompt - fail if not found
        print(f"Reading system prompt from: {system_prompt_path}")
        system_prompt = read_file_content(system_prompt_path)
        if not system_prompt or system_prompt.strip() == "":
            error_msg = f"System prompt file is empty or could not be read: {system_prompt_path}"
            print(f"✗ Error: {error_msg}")
            raise ValueError(error_msg)
        print(f"✓ Loaded system prompt ({len(system_prompt)} characters)")

        # Load user prompt template - fail if not found
        print(f"Reading user prompt template from: {user_prompt_template_path}")
        user_prompt_template = read_file_content(user_prompt_template_path)
        if not user_prompt_template or user_prompt_template.strip() == "":
            error_msg = f"User prompt template file is empty or could not be read: {user_prompt_template_path}"
            print(f"✗ Error: {error_msg}")
            raise ValueError(error_msg)
        print(f"✓ Loaded user prompt template ({len(user_prompt_template)} characters)")

        # Validate template has the required placeholder
        if '{USER_SCRIPT}' not in user_prompt_template:
            error_msg = f"User prompt template must contain '{{USER_SCRIPT}}' placeholder. Template: {user_prompt_template_path}"
            print(f"✗ Error: {error_msg}")
            raise ValueError(error_msg)

        # Format the user prompt
        print("Formatting user prompt with script content...")
        user_prompt = user_prompt_template.format(USER_SCRIPT=params_content)
        print(f"✓ User prompt formatted successfully ({len(user_prompt)} characters)")

        if debug:
            print(f"\n--- DEBUG INFO ---")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"User prompt length: {len(user_prompt)}")
            print(f"System prompt preview: {system_prompt[:200]}...")
            print(f"User prompt preview: {user_prompt[:200]}...")
            print(f"--- END DEBUG ---\n")

        print('Waiting for a response from Gemini...')
        print('This may take 30-60 seconds for complex analysis...')

        # Start progress counter
        stop_event = threading.Event()
        progress_thread = threading.Thread(target=progress_counter, args=(stop_event,))
        progress_thread.daemon = True
        progress_thread.start()

        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                config={
                    'temperature': 0.2,
                    'top_p': 0.7,
                    'top_k': 20,
                    'max_output_tokens': 4096,
                    'response_mime_type': 'application/json',
                    'response_schema': list[Output]
                }
            )

            if debug:
                print(f"\n--- DEBUG: Raw response ---")
                print(getattr(response, "text", "No text attribute"))
                print(f"--- END DEBUG ---\n")

            output = response.parsed
            stop_event.set()
            progress_thread.join(timeout=1)

            print('✓ Received response from Gemini!')
            
            # Write output to file
            if output:
                output_data = [o.model_dump() for o in output]
                write_file_content(output_path, output_data)
                print(f"✓ Output saved to: {output_path}")
                return True
            else:
                print("✗ No output received from Gemini")
                return False

        except Exception as api_error:
            stop_event.set()
            progress_thread.join(timeout=1)
            print(f"✗ Gemini API call failed: {api_error}")
            if debug:
                print(f"Traceback:\n{traceback.format_exc()}")
            raise api_error

    except Exception as e:
        print(f"✗ Gemini estimation failed: {e}")
        if debug:
            print(f"Full traceback:\n{traceback.format_exc()}")
        return False


if __name__ == '__main__':
    run_estimation()