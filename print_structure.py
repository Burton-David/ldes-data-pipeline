import os

def write_directory_structure(startpath, output_file):
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            f.write(f'{indent}{os.path.basename(root)}/\n')
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f'{subindent}{file}\n')

# Replace this with the path to your project directory
project_path = '/Users/davidburton/Sightline3'
output_file = os.path.join(project_path, 'project_structure.txt')

write_directory_structure(project_path, output_file)
print(f"Project structure has been saved to {output_file}")