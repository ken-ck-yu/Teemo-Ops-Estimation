import json
import time
import threading
from google import genai
from pydantic import BaseModel

# Import flexible I/O functions
from file_reader import read_file_content
from file_writer import write_file_content

class Output(BaseModel):
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
    seconds = 0
    while not stop_event.is_set():
        time.sleep(5)
        seconds += 5
        if not stop_event.is_set():
            print(f"Still waiting... ({seconds}s elapsed)")


def run_estimation_with_gemini(config):
    debug_mode = config.get('debug', False)

    try:
        client = genai.Client(api_key=config['api_key'])
        
        # Use flexible read function for prompt templates
        system_prompt = read_file_content(config['system_prompt'])
        user_prompt_template = read_file_content(config['user_prompt_template'])
        extracted_params = config['extracted_params']  # Now accepts content directly
        user_prompt = user_prompt_template.format(USER_SCRIPT=extracted_params)

        print('Waiting for a response from Gemini...')
        print('This may take 30-60 seconds for complex analysis...')

        stop_event = threading.Event()
        progress_thread = threading.Thread(target=progress_counter, args=(stop_event,))
        progress_thread.daemon = True
        progress_thread.start()

        try:
            response = client.models.generate_content(
                model=config['model'],
                contents=[
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                config={
                    'temperature': '0.2',
                    'top_p': '0.7',
                    'top_k':'20',
                    'max_output_tokens': '4096',
                    'response_mime_type': 'application/json',
                    'response_schema': list[Output]
                }
            )

            if debug_mode:
                print("Debug - Raw response:", getattr(response, "text", None))

            output = response.parsed
            stop_event.set()
            progress_thread.join(timeout=1)

            print('Received response from Gemini!')
            
            # Use flexible write function
            output_data = [o.model_dump() for o in output]
            write_file_content(config['output_file'], output_data)
            
            print(f"\nOutput saved to: {config['output_file']}")
            return True

        except Exception as e:
            stop_event.set()
            progress_thread.join(timeout=1)
            raise e

    except Exception as e:
        print(f"Gemini estimation failed: {e}")
        return False


def run_estimation(provider=None, params_content=None, output_path=None, debug=False, api_key=None, model=None, system_prompt=None, user_prompt_template=None):
    """Run the resource estimation process with Gemini.
    
    Args:
        provider: AI provider (must be 'gemini')
        params_content: The extracted parameters as a string (file content)
        output_path: Path to save the estimation results
        debug: Enable debug mode
        api_key: Gemini API key
        model: Gemini model name
        system_prompt: Path to system prompt file
        user_prompt_template: Path to user prompt template file
    """
    if provider != 'gemini':
        print(f"Only 'gemini' provider is supported")
        return False
    
    if not api_key:
        print(f"Missing API key for Gemini.")
        return False

    config = {
        'api_key': api_key,
        'model': model,
        'system_prompt': system_prompt,
        'user_prompt_template': user_prompt_template,
        'extracted_params': params_content,
        'output_file': output_path,
        'debug': debug,
    }
    return run_estimation_with_gemini(config)


if __name__ == '__main__':
    run_estimation()