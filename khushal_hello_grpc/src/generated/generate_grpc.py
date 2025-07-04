#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_grpc.py <proto_file> <output_dir>")
        sys.exit(1)
    
    proto_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Copy proto file to output directory
    import shutil
    proto_name = os.path.basename(proto_file)
    proto_copy = os.path.join(output_dir, proto_name)
    shutil.copy2(proto_file, proto_copy)
    
    # Create __init__.py
    init_file = os.path.join(output_dir, "__init__.py")
    with open(init_file, 'w') as f:
        f.write("")
    
    # Generate gRPC code using grpc_tools.protoc
    try:
        from grpc_tools import protoc
        
        # Change to output directory
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        # Run protoc with proper arguments
        protoc_args = [
            'grpc_tools.protoc',
            '-I.',
            '--python_out=.',
            '--grpc_python_out=.',
            proto_name
        ]
        
        result = protoc.main(protoc_args)
        
        if result != 0:
            print(f"protoc failed with exit code {result}")
            sys.exit(result)
        
        # Patch the generated grpc file
        grpc_file = proto_name.replace('.proto', '_pb2_grpc.py')
        if os.path.exists(grpc_file):
            with open(grpc_file, 'r') as f:
                content = f.read()
            
            # Fix the imports for both hello and user services
            if 'hello.proto' in proto_name:
                content = content.replace(
                    'import hello_pb2 as hello__pb2',
                    'from . import hello_pb2 as hello__pb2'
                )
            elif 'user.proto' in proto_name:
                content = content.replace(
                    'import user_pb2 as user__pb2',
                    'from . import user_pb2 as user__pb2'
                )
            
            with open(grpc_file, 'w') as f:
                f.write(content)
        
        os.chdir(original_cwd)
        print("gRPC code generation completed successfully")
        
    except ImportError as e:
        print(f"Error importing grpc_tools: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating gRPC code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 