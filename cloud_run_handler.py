#!/usr/bin/env python3
"""
Google Cloud Run HTTP Handler for BioM3
Handles HTTP requests and processes them through the BioM3 pipeline
"""

import json
import os
import sys
import tempfile
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add BioM3 to Python path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/BioM3')

app = Flask(__name__)
CORS(app, origins=['*'], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])

class CloudRunHandler:
    def __init__(self):
        """Initialize the Cloud Run handler"""
        self.container = None
        self.initialized = False
        
    def initialize_container(self):
        """Initialize the BioM3 container"""
        if not self.initialized:
            try:
                logger.info("Initializing BioM3 container...")
                # Import the BioM3 container
                from biom3_container import BioM3Container
                self.container = BioM3Container()
                self.initialized = True
                logger.info("BioM3 container initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize BioM3 container: {e}")
                raise
    
    def process_prompts(self, prompts, config=None):
        """Process prompts through the BioM3 pipeline"""
        if not self.initialized:
            self.initialize_container()
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for prompt in prompts:
                f.write(prompt + '\n')
            temp_input_file = f.name
        
        # Temporarily replace the input file
        original_input_file = "/app/input/prompts.txt"
        if os.path.exists(original_input_file):
            os.rename(original_input_file, original_input_file + ".backup")
        
        try:
            # Copy temp file to expected location
            import shutil
            shutil.copy2(temp_input_file, original_input_file)
            
            # Update container config if provided
            if config:
                self.container.config.update(config)
            
            # Run the pipeline
            self.container.run_pipeline()
            
            # Read results
            results = self.read_results()
            
            return results
            
        finally:
            # Clean up
            os.unlink(temp_input_file)
            if os.path.exists(original_input_file + ".backup"):
                os.rename(original_input_file + ".backup", original_input_file)
    
    def read_results(self):
        """Read the pipeline results"""
        results = {}
        
        # Read stage outputs
        output_dir = "/app/output"
        
        # Stage 1 embeddings
        stage1_file = f"{output_dir}/stage1_embeddings.json"
        if os.path.exists(stage1_file):
            with open(stage1_file, 'r') as f:
                results['stage1_embeddings'] = json.load(f)
        
        # Stage 2 embeddings
        stage2_file = f"{output_dir}/stage2_embeddings.json"
        if os.path.exists(stage2_file):
            with open(stage2_file, 'r') as f:
                results['stage2_embeddings'] = json.load(f)
        
        # Stage 3 sequences
        stage3_file = f"{output_dir}/stage3_sequences.json"
        if os.path.exists(stage3_file):
            with open(stage3_file, 'r') as f:
                results['stage3_sequences'] = json.load(f)
        
        # Pipeline summary
        summary_file = f"{output_dir}/pipeline_summary.txt"
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                results['pipeline_summary'] = f.read()
        
        return results

# Global handler instance
handler = CloudRunHandler()

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'service': 'BioM3 Cloud Run',
        'initialized': handler.initialized
    })

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    """Main prediction endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Parse request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate input
        if 'prompts' not in data:
            return jsonify({'error': 'Missing required field: prompts'}), 400
        
        prompts = data['prompts']
        if not isinstance(prompts, list) or len(prompts) == 0:
            return jsonify({'error': 'Prompts must be a non-empty list'}), 400
        
        # Get optional config
        config = data.get('config', {})
        
        # Validate config parameters
        if 'diffusion_steps' in config:
            if not isinstance(config['diffusion_steps'], int) or config['diffusion_steps'] <= 0:
                return jsonify({'error': 'diffusion_steps must be a positive integer'}), 400
        
        if 'num_replicas' in config:
            if not isinstance(config['num_replicas'], int) or config['num_replicas'] <= 0:
                return jsonify({'error': 'num_replicas must be a positive integer'}), 400
        
        logger.info(f"Processing {len(prompts)} prompts")
        
        # Process prompts
        results = handler.process_prompts(prompts, config)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'processed_prompts': len(prompts)
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """Batch prediction endpoint for multiple requests"""
    try:
        # Parse request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate input
        if 'requests' not in data:
            return jsonify({'error': 'Missing required field: requests'}), 400
        
        requests = data['requests']
        if not isinstance(requests, list) or len(requests) == 0:
            return jsonify({'error': 'Requests must be a non-empty list'}), 400
        
        results = []
        for i, req in enumerate(requests):
            try:
                if 'prompts' not in req:
                    results.append({
                        'index': i,
                        'error': 'Missing required field: prompts'
                    })
                    continue
                
                prompts = req['prompts']
                config = req.get('config', {})
                
                # Process this request
                result = handler.process_prompts(prompts, config)
                results.append({
                    'index': i,
                    'status': 'success',
                    'results': result
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results,
            'total_requests': len(requests)
        })
        
    except Exception as e:
        logger.error(f"Error processing batch request: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/info', methods=['GET', 'OPTIONS'])
def info():
    """Get service information"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'service': 'BioM3 Cloud Run',
        'version': '1.0.0',
        'description': 'BioM3 protein generation and structure prediction pipeline',
        'endpoints': {
            'health': '/health',
            'predict': '/predict',
            'predict_batch': '/predict/batch',
            'info': '/info'
        },
        'supported_configs': {
            'diffusion_steps': 'Number of diffusion steps (default: 1024)',
            'num_replicas': 'Number of sequence replicas to generate (default: 5)'
        }
    })

@app.route('/', methods=['GET'])
def root():
    """Serve the BioM3 web GUI"""
    try:
        # Try to serve the external HTML file
        with open('biom3_web_gui.html', 'r') as f:
            html_content = f.read()
        return html_content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        # Fallback to embedded HTML if file doesn't exist
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioM3 - Protein Generation & Structure Prediction</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .logo {
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient 3s ease infinite;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .subtitle {
            font-size: 1.2rem;
            color: #fff;
            opacity: 0.9;
            margin-bottom: 20px;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .input-section, .output-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }

        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }

        .preset-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .preset-btn {
            padding: 8px 16px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }

        .preset-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            flex: 1;
        }

        .btn-primary {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }

        .btn-secondary {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
        }

        .btn-secondary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        }

        .btn-info {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }

        .btn-info:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
        }

        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 500;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .output-content {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .logo {
                font-size: 2.5rem;
            }
            
            .action-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">BioM3</div>
            <div class="subtitle">Protein Generation & Structure Prediction Pipeline</div>
        </div>

        <div class="main-content">
            <div class="input-section">
                <h2 class="section-title">Input Configuration</h2>
                
                <div class="form-group">
                    <label for="prompt">Protein Description Prompt:</label>
                    <textarea id="prompt" rows="4" placeholder="Describe the protein you want to generate...">Generate a protein that can bind to DNA and regulate gene expression</textarea>
                </div>

                <div class="form-group">
                    <label for="diffusionSteps">Diffusion Steps:</label>
                    <input type="number" id="diffusionSteps" value="1024" min="1" max="2000">
                </div>

                <div class="form-group">
                    <label for="numReplicas">Number of Replicas:</label>
                    <input type="number" id="numReplicas" value="5" min="1" max="10">
                </div>

                <div class="preset-buttons">
                    <button class="preset-btn" onclick="setPreset('enzyme')">Enzyme</button>
                    <button class="preset-btn" onclick="setPreset('antibody')">Antibody</button>
                    <button class="preset-btn" onclick="setPreset('receptor')">Receptor</button>
                    <button class="preset-btn" onclick="setPreset('structural')">Structural</button>
                    <button class="preset-btn" onclick="setPreset('transport')">Transport</button>
                </div>

                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="generateProtein()">Generate Protein</button>
                    <button class="btn btn-info" onclick="checkHealth()">Check Health</button>
                    <button class="btn btn-secondary" onclick="getInfo()">Service Info</button>
                </div>

                <div id="status" class="status" style="display: none;"></div>
            </div>

            <div class="output-section">
                <h2 class="section-title">Results & Output</h2>
                <div id="loading" class="loading">
                    <div class="spinner"></div>
                    <p>Processing... This may take several minutes.</p>
                </div>
                <div id="output" class="output-content">
                    <p>Results will appear here after processing...</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>BioM3 Cloud Run Service | Powered by Advanced AI Models</p>
        </div>
    </div>

    <script>
        const API_BASE_URL = window.location.origin;
        
        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
        }

        function hideStatus() {
            document.getElementById('status').style.display = 'none';
        }

        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('output').innerHTML = '<p>Processing...</p>';
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }

        function updateOutput(content) {
            document.getElementById('output').innerHTML = content;
        }

        async function checkHealth() {
            try {
                showStatus('Checking service health...', 'info');
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();
                
                if (response.ok) {
                    showStatus('Service is healthy!', 'success');
                    updateOutput(JSON.stringify(data, null, 2));
                } else {
                    showStatus('Service health check failed', 'error');
                    updateOutput(JSON.stringify(data, null, 2));
                }
            } catch (error) {
                showStatus('Error checking health: ' + error.message, 'error');
                updateOutput('Error: ' + error.message);
            }
        }

        async function getInfo() {
            try {
                showStatus('Getting service information...', 'info');
                const response = await fetch(`${API_BASE_URL}/info`);
                const data = await response.json();
                
                if (response.ok) {
                    showStatus('Service info retrieved successfully', 'success');
                    updateOutput(JSON.stringify(data, null, 2));
                } else {
                    showStatus('Failed to get service info', 'error');
                    updateOutput(JSON.stringify(data, null, 2));
                }
            } catch (error) {
                showStatus('Error getting info: ' + error.message, 'error');
                updateOutput('Error: ' + error.message);
            }
        }

        async function generateProtein() {
            const prompt = document.getElementById('prompt').value.trim();
            const diffusionSteps = parseInt(document.getElementById('diffusionSteps').value);
            const numReplicas = parseInt(document.getElementById('numReplicas').value);

            if (!prompt) {
                showStatus('Please enter a protein description', 'error');
                return;
            }

            try {
                showStatus('Generating protein... This may take several minutes.', 'info');
                showLoading();
                hideStatus();

                const requestData = {
                    prompts: [prompt],
                    config: {
                        diffusion_steps: diffusionSteps,
                        num_replicas: numReplicas
                    }
                };

                const response = await fetch(`${API_BASE_URL}/predict`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();
                hideLoading();

                if (response.ok) {
                    showStatus('Protein generation completed successfully!', 'success');
                    updateOutput(JSON.stringify(data, null, 2));
                } else {
                    showStatus('Protein generation failed: ' + (data.error || 'Unknown error'), 'error');
                    updateOutput(JSON.stringify(data, null, 2));
                }
            } catch (error) {
                hideLoading();
                showStatus('Error generating protein: ' + error.message, 'error');
                updateOutput('Error: ' + error.message);
            }
        }

        function setPreset(type) {
            const presets = {
                enzyme: 'Generate an enzyme that catalyzes the breakdown of complex carbohydrates into simple sugars',
                antibody: 'Generate an antibody that specifically binds to viral surface proteins and neutralizes infection',
                receptor: 'Generate a cell surface receptor that responds to growth factors and initiates cell signaling pathways',
                structural: 'Generate a structural protein that provides mechanical support and maintains cell shape',
                transport: 'Generate a membrane transport protein that facilitates the movement of ions across cell membranes'
            };
            
            document.getElementById('prompt').value = presets[type] || '';
        }

        // Initialize by checking health
        window.onload = function() {
            checkHealth();
        };
    </script>
</body>
</html>'''
    
    return html_content, 200, {'Content-Type': 'text/html'}

if __name__ == '__main__':
    # Initialize the handler
    try:
        logger.info("Starting BioM3 Cloud Run service...")
        handler.initialize_container()
    except Exception as e:
        logger.error(f"Failed to initialize handler: {e}")
        # Continue anyway - will initialize on first request
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 