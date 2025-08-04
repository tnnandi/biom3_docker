#!/usr/bin/env python3
"""
BioM3 GUI Application
A graphical user interface for the BioM3 protein design pipeline
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import json
import sys
from pathlib import Path
import webbrowser

class BioM3GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BioM3 - Protein Design Pipeline")
        self.root.geometry("800x600")
        
        # Configuration
        self.docker_username = "tnnandi"
        self.image_name = "biom3"
        self.version = "v1.1"
        
        # Default parameters
        self.diffusion_steps = tk.IntVar(value=256)
        self.num_replicas = tk.IntVar(value=2)
        
        # Status variables
        self.setup_complete = False
        self.container_downloaded = False
        self.weights_downloaded = False
        
        self.create_widgets()
        self.check_setup_status()
    
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup tab
        self.setup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_frame, text="Setup")
        self.create_setup_tab()
        
        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.create_config_tab()
        
        # Run tab
        self.run_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.run_frame, text="Run Pipeline")
        self.create_run_tab()
        
        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.create_results_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_setup_tab(self):
        # Setup instructions
        setup_label = ttk.Label(self.setup_frame, text="BioM3 Setup", font=("Arial", 16, "bold"))
        setup_label.pack(pady=10)
        
        # Docker section
        docker_frame = ttk.LabelFrame(self.setup_frame, text="Docker Container", padding=10)
        docker_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.docker_status = tk.StringVar(value="Checking...")
        docker_status_label = ttk.Label(docker_frame, textvariable=self.docker_status)
        docker_status_label.pack()
        
        self.download_container_btn = ttk.Button(docker_frame, text="Download Container", 
                                               command=self.download_container)
        self.download_container_btn.pack(pady=5)
        
        # Weights section
        weights_frame = ttk.LabelFrame(self.setup_frame, text="Model Weights", padding=10)
        weights_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.weights_status = tk.StringVar(value="Checking...")
        weights_status_label = ttk.Label(weights_frame, textvariable=self.weights_status)
        weights_status_label.pack()
        
        self.download_weights_btn = ttk.Button(weights_frame, text="Download Weights (~5.5GB)", 
                                             command=self.download_weights)
        self.download_weights_btn.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.setup_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Log area
        log_frame = ttk.LabelFrame(self.setup_frame, text="Setup Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_config_tab(self):
        # Parameters section
        params_frame = ttk.LabelFrame(self.config_frame, text="Generation Parameters", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Diffusion steps
        ttk.Label(params_frame, text="Diffusion Steps:").grid(row=0, column=0, sticky=tk.W, pady=5)
        diffusion_spin = ttk.Spinbox(params_frame, from_=100, to=2000, textvariable=self.diffusion_steps, width=10)
        diffusion_spin.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(params_frame, text="(Number of diffusion steps for sequence generation, default: 256)").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Number of replicas
        ttk.Label(params_frame, text="Number of Replicas:").grid(row=1, column=0, sticky=tk.W, pady=5)
        replicas_spin = ttk.Spinbox(params_frame, from_=1, to=20, textvariable=self.num_replicas, width=10)
        replicas_spin.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(params_frame, text="(Number of replicas for sequence generation, default: 2)").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # Quick presets
        presets_frame = ttk.LabelFrame(self.config_frame, text="Quick Presets", padding=10)
        presets_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(presets_frame, text="Fast Test (256 steps, 2 replicas)", 
                  command=lambda: self.set_preset(256, 2)).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_frame, text="Standard (1024 steps, 5 replicas)", 
                  command=lambda: self.set_preset(1024, 5)).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_frame, text="High Quality (2048 steps, 10 replicas)", 
                  command=lambda: self.set_preset(2048, 10)).pack(side=tk.LEFT, padx=5)
    
    def create_run_tab(self):
        # Prompt input
        prompt_frame = ttk.LabelFrame(self.run_frame, text="Protein Description", padding=10)
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        prompt_label = ttk.Label(prompt_frame, text="Enter your protein description:")
        prompt_label.pack(anchor=tk.W)
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=8)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Example prompt
        example_frame = ttk.LabelFrame(self.run_frame, text="Example Prompts", padding=10)
        example_frame.pack(fill=tk.X, padx=10, pady=5)
        
        examples = [
            "Translation initiation factor IF-1",
            "Green fluorescent protein",
            "Insulin hormone"
        ]
        
        for example in examples:
            btn = ttk.Button(example_frame, text=example, 
                           command=lambda e=example: self.load_example(e))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Run button
        self.run_btn = ttk.Button(self.run_frame, text="Run BioM3 Pipeline", 
                                 command=self.run_pipeline, style="Accent.TButton")
        self.run_btn.pack(pady=10)
        
        # Run log
        run_log_frame = ttk.LabelFrame(self.run_frame, text="Pipeline Log", padding=10)
        run_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.run_log = scrolledtext.ScrolledText(run_log_frame, height=6)
        self.run_log.pack(fill=tk.BOTH, expand=True)
    
    def create_results_tab(self):
        # Results navigation
        nav_frame = ttk.Frame(self.results_frame)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(nav_frame, text="Refresh Results", 
                  command=self.refresh_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Open Output Folder", 
                  command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(self.results_frame, text="Generated Sequences", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Load initial results
        self.refresh_results()
    
    def check_setup_status(self):
        """Check if container and weights are already downloaded"""
        def check():
            # Check container
            try:
                result = subprocess.run(['docker', 'images', f'{self.docker_username}/{self.image_name}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and self.docker_username in result.stdout:
                    self.container_downloaded = True
                    self.docker_status.set("✓ Container downloaded")
                    self.download_container_btn.config(state='disabled')
                else:
                    self.docker_status.set("✗ Container not found")
            except:
                self.docker_status.set("✗ Docker not available")
            
            # Check weights
            weights_exist = (
                os.path.exists('weights/PenCL/BioM3_PenCL_epoch20.bin') and
                os.path.exists('weights/Facilitator/BioM3_Facilitator_epoch20.bin') and
                os.path.exists('weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin')
            )
            
            if weights_exist:
                self.weights_downloaded = True
                self.weights_status.set("✓ Weights downloaded")
                self.download_weights_btn.config(state='disabled')
            else:
                self.weights_status.set("✗ Weights not found")
            
            self.setup_complete = self.container_downloaded and self.weights_downloaded
            self.update_status()
        
        threading.Thread(target=check, daemon=True).start()
    
    def download_container(self):
        """Download the Docker container"""
        def download():
            self.log_message("Starting container download...")
            self.progress_var.set(10)
            
            try:
                # Pull the container
                cmd = ['docker', 'pull', f'{self.docker_username}/{self.image_name}:{self.version}']
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        text=True, bufsize=1, universal_newlines=True)
                
                for line in process.stdout:
                    self.log_message(line.strip())
                    if "Downloaded" in line or "Pulled" in line:
                        self.progress_var.set(100)
                
                process.wait()
                
                if process.returncode == 0:
                    self.container_downloaded = True
                    self.docker_status.set("✓ Container downloaded")
                    self.download_container_btn.config(state='disabled')
                    self.log_message("Container download completed successfully!")
                else:
                    self.log_message("Container download failed!")
                    
            except Exception as e:
                self.log_message(f"Error downloading container: {e}")
            
            self.update_status()
        
        threading.Thread(target=download, daemon=True).start()
    
    def download_weights(self):
        """Download the model weights"""
        def download():
            self.log_message("Starting weights download...")
            self.progress_var.set(10)
            
            try:
                # Create directories
                os.makedirs('weights/LLMs', exist_ok=True)
                os.makedirs('weights/PenCL', exist_ok=True)
                os.makedirs('weights/Facilitator', exist_ok=True)
                os.makedirs('weights/ProteoScribe', exist_ok=True)
                
                self.progress_var.set(20)
                
                # Download weights using the existing script
                cmd = ['./download_weights.sh']
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        text=True, bufsize=1, universal_newlines=True)
                
                for line in process.stdout:
                    self.log_message(line.strip())
                    if "Downloading" in line:
                        self.progress_var.set(30)
                    elif "Successfully" in line or "already exists" in line:
                        self.progress_var.set(80)
                
                process.wait()
                
                if process.returncode == 0:
                    self.weights_downloaded = True
                    self.weights_status.set("✓ Weights downloaded")
                    self.download_weights_btn.config(state='disabled')
                    self.log_message("Weights download completed successfully!")
                else:
                    self.log_message("Weights download failed!")
                    
            except Exception as e:
                self.log_message(f"Error downloading weights: {e}")
            
            self.progress_var.set(100)
            self.update_status()
        
        threading.Thread(target=download, daemon=True).start()
    
    def set_preset(self, diffusion_steps, num_replicas):
        """Set parameter preset"""
        self.diffusion_steps.set(diffusion_steps)
        self.num_replicas.set(num_replicas)
        messagebox.showinfo("Preset Applied", f"Set to {diffusion_steps} diffusion steps and {num_replicas} replicas")
    
    def load_example(self, example):
        """Load example prompt"""
        examples = {
            "Translation initiation factor IF-1": 
                "PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.",
            "Green fluorescent protein": 
                "PROTEIN NAME: Green fluorescent protein. FUNCTION: A protein that exhibits bright green fluorescence when exposed to light in the blue to ultraviolet range. The protein has a beta-barrel structure with 11 beta strands and an alpha helix running through the center. The chromophore is formed by autocatalytic cyclization and oxidation of three amino acids.",
            "Insulin hormone": 
                "PROTEIN NAME: Insulin. FUNCTION: A peptide hormone that regulates glucose metabolism. It consists of two polypeptide chains (A and B) linked by disulfide bonds. The A chain has 21 amino acids and the B chain has 30 amino acids. It promotes glucose uptake by cells and inhibits glucose production in the liver."
        }
        
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, examples[example])
    
    def run_pipeline(self):
        """Run the BioM3 pipeline"""
        if not self.setup_complete:
            messagebox.showerror("Setup Required", "Please complete the setup first (download container and weights)")
            return
        
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showerror("Input Required", "Please enter a protein description")
            return
        
        def run():
            self.run_btn.config(state='disabled')
            self.run_log.delete(1.0, tk.END)
            self.log_run_message("Starting BioM3 pipeline...")
            
            try:
                # Create input directory and write prompt
                os.makedirs('input', exist_ok=True)
                with open('input/prompts.txt', 'w') as f:
                    f.write(prompt)
                
                # Create output directory
                os.makedirs('output', exist_ok=True)
                
                # Run the container
                cmd = [
                    'docker', 'run',
                    '-e', f'DIFFUSION_STEPS={self.diffusion_steps.get()}',
                    '-e', f'NUM_REPLICAS={self.num_replicas.get()}',
                    '-v', f'{os.getcwd()}/input:/app/input',
                    '-v', f'{os.getcwd()}/output:/app/output',
                    '-v', f'{os.getcwd()}/weights:/app/weights',
                    f'{self.docker_username}/{self.image_name}:{self.version}'
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        text=True, bufsize=1, universal_newlines=True)
                
                for line in process.stdout:
                    self.log_run_message(line.strip())
                
                process.wait()
                
                if process.returncode == 0:
                    self.log_run_message("Pipeline completed successfully!")
                    messagebox.showinfo("Success", "BioM3 pipeline completed! Check the Results tab.")
                    self.refresh_results()
                else:
                    self.log_run_message("Pipeline failed!")
                    messagebox.showerror("Error", "Pipeline failed. Check the log for details.")
                    
            except Exception as e:
                self.log_run_message(f"Error running pipeline: {e}")
                messagebox.showerror("Error", f"Failed to run pipeline: {e}")
            
            self.run_btn.config(state='normal')
        
        threading.Thread(target=run, daemon=True).start()
    
    def refresh_results(self):
        """Refresh the results display"""
        self.results_text.delete(1.0, tk.END)
        
        if not os.path.exists('output'):
            self.results_text.insert(tk.END, "No output directory found. Run the pipeline first.")
            return
        
        # Look for sequence files
        sequence_files = []
        for file in os.listdir('output'):
            if file.endswith('.json') and 'sequences' in file:
                sequence_files.append(file)
        
        if not sequence_files:
            self.results_text.insert(tk.END, "No results found. Run the pipeline first.")
            return
        
        # Load and display results
        for file in sequence_files:
            try:
                with open(f'output/{file}', 'r') as f:
                    data = json.load(f)
                
                self.results_text.insert(tk.END, f"=== {file} ===\n")
                if isinstance(data, list):
                    for i, item in enumerate(data, 1):
                        if isinstance(item, dict) and 'sequence' in item:
                            self.results_text.insert(tk.END, f"Sequence {i}:\n{item['sequence']}\n\n")
                        else:
                            self.results_text.insert(tk.END, f"Item {i}: {str(item)[:100]}...\n\n")
                else:
                    self.results_text.insert(tk.END, f"{str(data)[:500]}...\n\n")
                    
            except Exception as e:
                self.results_text.insert(tk.END, f"Error reading {file}: {e}\n\n")
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        output_path = os.path.abspath('output')
        if os.path.exists(output_path):
            if sys.platform == "darwin":  # macOS
                subprocess.run(['open', output_path])
            elif sys.platform == "win32":  # Windows
                subprocess.run(['explorer', output_path])
            else:  # Linux
                subprocess.run(['xdg-open', output_path])
        else:
            messagebox.showinfo("No Output", "Output folder doesn't exist yet. Run the pipeline first.")
    
    def log_message(self, message):
        """Add message to setup log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def log_run_message(self, message):
        """Add message to run log"""
        self.run_log.insert(tk.END, f"{message}\n")
        self.run_log.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self):
        """Update status bar"""
        if self.setup_complete:
            self.status_var.set("Ready to run pipeline")
        else:
            self.status_var.set("Setup required")

def main():
    root = tk.Tk()
    app = BioM3GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 