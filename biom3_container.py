#!/usr/bin/env python3
"""
BioM3 Containerized Pipeline
Handles the complete pipeline from text prompts to protein structures
"""

import json
import os
import sys
import torch
import pandas as pd
import numpy as np
from argparse import Namespace

# Add BioM3 to Python path
sys.path.insert(0, '/app/BioM3')

# Fix to resolve the weights loading issue with PyTorch 2.6
import torch.serialization
from argparse import Namespace
torch.serialization.add_safe_globals([Namespace])

# Import the required modules
import Stage1_source.model as Stage1_mod
import Stage3_source.cond_diff_transformer_layer as cdtl
import Stage3_source.sampling_analysis as Stage3_sample_tools
import Stage3_source.animation_tools as Stage3_ani_tools
# except ImportError as e:
#     print(f"Import error: {e}")
#     print("Available modules in /app/BioM3:")
#     import os
#     for root, dirs, files in os.walk('/app/BioM3'):
#         for file in files:
#             if file.endswith('.py'):
#                 print(f"  {os.path.join(root, file)}")
#     sys.exit(1)

class BioM3Container:
    def __init__(self, config=None):
        self.config = config or self.load_default_config()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Load configurations
        self.load_configs()
        
        # Load prompts
        self.prompts = self.load_prompts()
        
    def load_default_config(self):
        """Load default configuration"""
        return {
            'diffusion_steps': int(os.environ.get('DIFFUSION_STEPS', 1024)),
            'num_replicas': int(os.environ.get('NUM_REPLICAS', 5))
        }

    def load_configs(self):
        """Load configuration files for all stages"""
        # Stage 1 config
        with open('/app/BioM3/stage1_config.json', 'r') as f:
            stage1_config_dict = json.load(f)
        self.stage1_config = self.convert_to_namespace(stage1_config_dict)
        
        # Stage 2 config
        with open('/app/BioM3/stage2_config.json', 'r') as f:
            stage2_config_dict = json.load(f)
        self.stage2_config = self.convert_to_namespace(stage2_config_dict)
        
        # Stage 3 config
        with open('/app/BioM3/stage3_config.json', 'r') as f:
            stage3_config_dict = json.load(f)
        self.stage3_config = self.convert_to_namespace(stage3_config_dict)
        
    # to make the config dictionary into a namespace so that the config can be accessed as an object
    # e.g., config.diffusion_steps, config.num_replicas instead of config['diffusion_steps'], config['num_replicas'] to make it compatible with the original code
    def convert_to_namespace(self, config_dict):
        """Convert dictionary to Namespace"""
        for key, value in config_dict.items():
            if isinstance(value, dict):
                config_dict[key] = self.convert_to_namespace(value)
        return Namespace(**config_dict)
        
    def load_prompts(self):
        """Load prompts from input file"""
        input_file = "/app/input/prompts.txt"
        if not os.path.exists(input_file):
            # # Create example prompt if file doesn't exist
            # os.makedirs("/app/input", exist_ok=True)
            # with open(input_file, 'w') as f:
            #     f.write("PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.\n")
            print(f"Error: Prompt file not found at {input_file}")
            sys.exit(1)
        with open(input_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
        
    def run_stage1(self, test_df):
        """Run Stage 1: PenCL - Generate text and protein embeddings"""
        print("Running Stage 1: PenCL...")
        
        # Load the PenCL model
        pencl_model = Stage1_mod.pfam_PEN_CL(args=self.stage1_config)
        
        # Load state dict with compatibility handling
        state_dict = torch.load('/app/weights/PenCL/BioM3_PenCL_epoch20.bin', map_location=self.device)
        
        # # Filter out incompatible keys
        # # TODO: This is a hack to get the model to load. We need to find a better way to do this.
        # model_state_dict = pencl_model.state_dict()
        # filtered_state_dict = {}
        # for key, value in state_dict.items():
        #     if key in model_state_dict:
        #         filtered_state_dict[key] = value
        #     else:
        #         print(f"Skipping incompatible key: {key}")

        filtered_state_dict = state_dict
        
        # Load the filtered state dict
        pencl_model.load_state_dict(filtered_state_dict, strict=False)
        pencl_model.to(self.device)
        pencl_model.eval()
        
        # Process each prompt
        results = []
        with torch.no_grad():
            for item in test_df.to_dict('records'):
                prompt_text = item['[final]text_caption']
                
                # Tokenize the text prompt
                tokenizer = pencl_model.text_encoder.tokenizer
                inputs = tokenizer(prompt_text, return_tensors='pt', padding=True, truncation=True, max_length=512)
                inputs = inputs.to(self.device)
                
                # Generate text embeddings using the PenCL model
                # We need to pass both text and protein inputs to get the projected embeddings
                # For inference, we'll use dummy protein sequences
                dummy_protein = torch.zeros(1, 1024).long().to(self.device)  # Dummy protein tokens
                
                # Get the projected embeddings from PenCL
                outputs = pencl_model(inputs['input_ids'], dummy_protein, compute_masked_logits=False)
                text_embeddings = outputs['text_joint_latent']  # This should be 512-dim
                
                results.append({
                    'prompt': prompt_text,
                    'text_embedding': text_embeddings.cpu().numpy(),
                })
                
        return results
        
    def run_stage2(self, stage1_output):
        """Run Stage 2: Facilitator - Generate facilitated embeddings"""
        print("Running Stage 2: Facilitator...")
        
        # Load the Facilitator model
        facilitator_model = Stage1_mod.Facilitator(
            in_dim=self.stage2_config.emb_dim,
            hid_dim=self.stage2_config.hid_dim,
            out_dim=self.stage2_config.emb_dim,
            dropout=self.stage2_config.dropout
        )
        
        # Load state dict with compatibility handling
        state_dict = torch.load('/app/weights/Facilitator/BioM3_Facilitator_epoch20.bin', map_location=self.device)
        
        # # Filter out incompatible keys
        # model_state_dict = facilitator_model.state_dict()
        # filtered_state_dict = {}
        # for key, value in state_dict.items():
        #     if key in model_state_dict:
        #         filtered_state_dict[key] = value
        #     else:
        #         print(f"Skipping incompatible key: {key}")

        filtered_state_dict = state_dict

        # Load the filtered state dict
        facilitator_model.load_state_dict(filtered_state_dict, strict=False)
        facilitator_model.to(self.device)
        facilitator_model.eval()
        
        # Process each prompt
        results = []
        with torch.no_grad():
            for item in stage1_output:
                # Convert embeddings to tensors
                text_emb = torch.tensor(item['text_embedding']).to(self.device) 
                
                # Get facilitated embedding
                facilitated_emb = facilitator_model(text_emb)
                
                results.append({
                    'prompt': item['prompt'],
                    'facilitated_embedding': facilitated_emb.cpu().numpy()
                })
                
        return results
        
    def run_stage3(self, stage2_output):
        """Run Stage 3: ProteoScribe - Generate protein sequences using facilitated embeddings"""
        print("Running Stage 3: ProteoScribe...")
        
        # Get config parameters
        diffusion_steps = self.config.get('diffusion_steps', self.stage3_config.diffusion_steps)
        num_replicas = self.config.get('num_replicas', self.stage3_config.num_replicas)
        
        print(f"Using diffusion_steps: {diffusion_steps}")
        print(f"Using num_replicas: {num_replicas}")
        
        # Get the ProteoScribe model using the get_model function
        data_shape = (self.stage3_config.image_size, self.stage3_config.image_size)  # Uses image_size
        num_classes = self.stage3_config.num_classes
        
        proteoscribe_model = cdtl.get_model(self.stage3_config, data_shape, num_classes)
        
        # Load state dict with compatibility handling
        state_dict = torch.load('/app/weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin', map_location=self.device)
        
        # # Filter out incompatible keys
        # model_state_dict = proteoscribe_model.state_dict()
        # filtered_state_dict = {}
        # for key, value in state_dict.items():
        #     if key in model_state_dict:
        #         filtered_state_dict[key] = value
        #     else:
        #         print(f"Skipping incompatible key: {key}")

        filtered_state_dict = state_dict
        
        # Load the filtered state dict
        proteoscribe_model.load_state_dict(filtered_state_dict, strict=False)
        proteoscribe_model.to(self.device)
        proteoscribe_model.eval()
        
        # Amino acid tokenization including special characters
        tokens = [
            '-', '<START>', 'A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M',
            'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y', '<END>', '<PAD>',
            'X', 'U', 'Z', 'B', 'O'  # Special characters
        ]
        
        # Process each prompt
        results = []
        with torch.no_grad():
            for item in stage2_output:
                # Convert facilitated embedding to tensor
                facilitated_emb = torch.tensor(item['facilitated_embedding']).to(self.device)
                
                # Generate sequences using the diffusion model
                sequences = self.generate_sequences_with_diffusion(
                    model=proteoscribe_model,
                    facilitated_emb=facilitated_emb,
                    num_replicas=num_replicas,
                    diffusion_steps=diffusion_steps,
                    tokens=tokens
                )
                
                results.append({
                    'prompt': item['prompt'],
                    'sequences': sequences,
                    'config': {
                        'diffusion_steps': diffusion_steps,
                        'num_replicas': num_replicas
                    }
                })
                
        return results
        
    def generate_sequences_with_diffusion(self, model, facilitated_emb, num_replicas, diffusion_steps, tokens):
        """Generate protein sequences using proper diffusion sampling"""
        sequences = []
        
        # Create args object for the sampling functions
        class Args:
            def __init__(self, device, diffusion_steps, num_replicas):
                self.device = device
                self.diffusion_steps = diffusion_steps
                self.num_replicas = num_replicas
                # self.batch_size_sample = 1  # Process one at a time for simplicity
        
        args = Args(self.device, diffusion_steps, num_replicas)
        
        # Generate sequences for each replica
        for replica_idx in range(num_replicas):
            # Set different random seed for each replica
            torch.manual_seed(replica_idx + 42)
            
            # Prepare input for the diffusion model
            # The facilitated embedding should condition the generation
            z_t = facilitated_emb.unsqueeze(0)  # Add batch dimension
            
            # Generate random sampling path
            sampling_path = torch.randperm(diffusion_steps)
            
            # Use the batch generation function from the original code
            mask_realization_list, _ = Stage3_sample_tools.batch_generate_denoised_sampled(
                args=args,
                model=model,
                extract_digit_samples=torch.zeros(1, diffusion_steps),
                extract_time=torch.zeros(1).long(),
                extract_digit_label=z_t,
                sampling_path=sampling_path.unsqueeze(0)
            )
            
            # Convert the generated numeric sequence to amino acid sequence
            if mask_realization_list and len(mask_realization_list) > 0:
                mask_realization = mask_realization_list[-1][0]  # Get the final realization
                sequence = Stage3_ani_tools.convert_num_to_char(tokens, mask_realization[0])
                # Clean the sequence
                clean_sequence = sequence.replace('<START>', '').replace('<END>', '').replace('<PAD>', '')
                sequences.append(clean_sequence)
            else:
                # Fallback if generation fails
                sequences.append("M" + "A" * 99)
        
        return sequences
        
    def predict_structures(self, stage3_output):
        """Predict protein structures using ESMFold"""
        print("Predicting protein structures...")
        
        # Import ESMFold
        from esm import pretrained
        import tempfile
        import subprocess
        
        results = []
        for item in stage3_output:
            prompt = item['prompt']
            sequences = item['sequences']
            
            print(f"Predicting structures for prompt: {prompt[:50]}...")
            
            # Create output directory for this prompt
            prompt_dir = f"/app/output/structures_{hash(prompt) % 10000}"
            os.makedirs(prompt_dir, exist_ok=True)
            
            # Predict structure for each sequence
            for i, seq in enumerate(sequences):
                try:
                    # Load ESMFold model
                    model, alphabet = pretrained.esmfold_v1()
                    model = model.eval()
                    
                    # Predict structure
                    with torch.no_grad():
                        output = model.infer_pdb(seq)
                    
                    # Save PDB file
                    pdb_file = f"{prompt_dir}/structure_{i+1}.pdb"
                    with open(pdb_file, 'w') as f:
                        f.write(output)
                        
                    print(f"Saved structure {i+1} to {pdb_file}")
                    
                except Exception as e:
                    print(f"Error predicting structure for sequence {i+1}: {e}")
                    
            results.append({
                'prompt': prompt,
                'structures_dir': prompt_dir
            })
            
        return results
        
    def save_stage_outputs(self, stage1_output, stage2_output, stage3_output):
        """Save intermediate outputs from each stage"""
        output_dir = "/app/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save Stage 1 outputs (text embeddings)
        stage1_file = f"{output_dir}/stage1_embeddings.json"
        stage1_data = []
        for item in stage1_output:
            stage1_data.append({
                'prompt': item['prompt'],
                'text_embedding_shape': item['text_embedding'].shape,
            })
        with open(stage1_file, 'w') as f:
            json.dump(stage1_data, f, indent=2)
        print(f"Stage 1 outputs saved to {stage1_file}")
        
        # Save Stage 2 outputs (facilitated embeddings)
        stage2_file = f"{output_dir}/stage2_embeddings.json"
        stage2_data = []
        for item in stage2_output:
            stage2_data.append({
                'prompt': item['prompt'],
                'facilitated_embedding_shape': item['facilitated_embedding'].shape
            })
        with open(stage2_file, 'w') as f:
            json.dump(stage2_data, f, indent=2)
        print(f"Stage 2 outputs saved to {stage2_file}")
        
        # Save Stage 3 outputs (generated sequences)
        stage3_file = f"{output_dir}/stage3_sequences.json"
        stage3_data = []
        for item in stage3_output:
            stage3_data.append({
                'prompt': item['prompt'],
                'sequences': item['sequences'],
                'config': item.get('config', {})
            })
        with open(stage3_file, 'w') as f:
            json.dump(stage3_data, f, indent=2)
        print(f"Stage 3 outputs saved to {stage3_file}")
        
    def run_pipeline(self):
        """Run the complete BioM3 pipeline"""
        print("Starting BioM3 Pipeline...")
        
        # Create dummy dataframe for stage 1 with correct column names
        test_df = pd.DataFrame({
            'protein_sequence': ['M' * 100] * len(self.prompts),
            '[final]text_caption': self.prompts,  
            'primary_Accession': [f'prompt_{i}' for i in range(len(self.prompts))]  
        })
        
        # Run all stages
        stage1_output = self.run_stage1(test_df)
        stage2_output = self.run_stage2(stage1_output)
        stage3_output = self.run_stage3(stage2_output)
        
        # Save intermediate outputs
        self.save_stage_outputs(stage1_output, stage2_output, stage3_output)
        
        # Predict structures
        structure_results = self.predict_structures(stage3_output)
        
        # Save results
        self.save_results(structure_results)
        
        print("Pipeline complete! Check /app/output for results.")
        
    def save_results(self, results):
        """Save pipeline results"""
        output_dir = "/app/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save summary
        summary_file = f"{output_dir}/pipeline_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("BioM3 Pipeline Results\n")
            f.write("======================\n\n")
            
            for result in results:
                f.write(f"Prompt: {result['prompt']}\n")
                f.write(f"Structures saved in: {result['structures_dir']}\n")
                f.write("-" * 50 + "\n")
                
        print(f"Results saved to {output_dir}")

def main():
    # Parse command line arguments for inference parameters
    import argparse
    parser = argparse.ArgumentParser(description='BioM3 Container with Inference Parameters')
    parser.add_argument('--diffusion_steps', type=int, default=1024, 
                       help='Number of diffusion steps (default: 1024)')
    parser.add_argument('--num_replicas', type=int, default=5, 
                       help='Number of sequence replicas to generate (default: 5)')
    parser.add_argument('--config_file', type=str, 
                       help='Path to JSON config file')
    
    args = parser.parse_args()
    
    # Load config
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {
            'diffusion_steps': args.diffusion_steps,
            'num_replicas': args.num_replicas
        }
    
    # Override with environment variables if present
    if os.environ.get('DIFFUSION_STEPS'):
        config['diffusion_steps'] = int(os.environ.get('DIFFUSION_STEPS'))
    if os.environ.get('NUM_REPLICAS'):
        config['num_replicas'] = int(os.environ.get('NUM_REPLICAS'))
    
    print(f"Using config: {config}")
    
    container = BioM3Container(config)
    container.run_pipeline()

if __name__ == "__main__":
    main() 