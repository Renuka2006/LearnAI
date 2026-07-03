import subprocess
import os
#import json
from google import genai
from google.genai import types
from pydantic import BaseModel
import glob
from typing import List

class FileEdit(BaseModel):
    filepath: str
    fixed_code: str

class TerraformFix(BaseModel):
    explanation: str
    #fixed_code: str
    edits: List[FileEdit]

def find_tf_files():
    tf_dirs = set()
    for tf_file in glob.glob("**/*.tf", recursive=True):
        if ".terraform" in tf_file or ".git" in tf_file:
            continue
        dirname = os.path.dirname(tf_file)
        tf_dirs.add(dirname if dirname else ".")
    return sorted(list(tf_dirs))

def load_all_tf_files(target_dir):
    tf_contents = []
    search_path = os.path.join(target_dir, "**/*.tf")
    for filepath in glob.glob(search_path, recursive=True):
        try:
            with open(filepath, "r") as f:
                content = f.read()
                tf_contents.append(f"filepath: {filepath}----\n----{content}\n----")
        except Exception as e:
            print(f"Warning: Error reading {filepath}: {e}")   
    return "\n\n".join(tf_contents)

def ask_gemini_to_fix(entire_codebase, error_logs, target_dir):
    print(f"[{target_dir}] Sending the logs to Gemini for analysis and fix...")
    client = genai.Client()
    system_instruction = ("You are an expert Site Reliability Engineer and automated patching agent. "
                          "Your job is to analyze broken Terraform configurations and logs, determine the root cause, "
                          "and provide the corrected codebase. Do not provide conversational responses outside the requested schema.")
    user_prompt = f"""The following Terraform code is failing validation:
    ---
    {target_dir}
    ---
    {entire_codebase}
    ---
    Here is the exact terminal error log:
    ---
    {error_logs}
    ---
    Please fix the syntax and logical issues in the configuration.
    """
    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = user_prompt,
        config = types.GenerateContentConfig(
            system_instruction = system_instruction,
            response_mime_type="application/json",
            response_schema=TerraformFix,
            temperature=0.1)
    )
    return response.parsed

def terraform_init(target_dir):
    print(f"[{target_dir}] Running 'terraform init'...")
    result = subprocess.run(["terraform", "init"], cwd=target_dir, capture_output=True, text=True)
    err_logs = result.stderr if result.stderr else result.stdout
    if result.returncode != 0:
        print(f"Terraform initialization failed in {target_dir}. Please check the error messages below:")
        print(err_logs)
        exit(1)
    else:
        print("Terraform initialization completed successfully.")
    return True, None

def needs_init(target_dir):
    return not os.path.isdir(os.path.join(target_dir, ".terraform"))

def run_terraform_validation(target_dir):
    #terraform_init(target_dir)
    print(f"{target_dir} Running Terraform validation...")
    result = subprocess.run(["terraform", "validate"], cwd=target_dir, capture_output=True, text=True)
    #print(result.stderr,result.stdout)

    if result.returncode != 0:
        print("TF Validation has Failed. Please check the error messages below:")
        err_logs = result.stderr if result.stderr else result.stdout
        return False, err_logs

    print("TF Validation has Passed!!!")
    return True, None

def patch_dir(target_dir, max_retries=3):
    retry_count = 0
    fix_applied = False
    fixed_successfully = False
    print(f"\n=========================================\nProcessing Directory: {target_dir}\n=========================================")

    while retry_count <= max_retries:
        codebase_context =load_all_tf_files(target_dir)
        if not codebase_context:
            print(f"""No Terraform files found in the directory '{target_dir}'. Please ensure you are in the correct directory.""")
            return False, False
        if needs_init(target_dir):
            init_success, logs = terraform_init(target_dir)
        else:
            print(f"[{target_dir}] Terraform already initialized, skipping init.")
            init_success, logs = True, None
        if init_success:
            validation_success, logs = run_terraform_validation(target_dir)
            is_config_valid = validation_success
        else:
            is_config_valid = False
        if is_config_valid:
            if retry_count > 0:
                print(f"[{target_dir}] Terraform configuration is valid after applying the fix.")
            else:
                print(f"[{target_dir}] Terraform configuration is valid. No fixes needed.")
            return True, True
        print(f"\n[Attempt {retry_count + 1}/{max_retries + 1}] Fix required for '{target_dir}'...")
        data = ask_gemini_to_fix(codebase_context, logs, target_dir)
        print("Explanation of the Issue:")
        print("--------------------------------------------")
        print(data.explanation)
        print("--------------------------------------------")
        for edits in data.edits:
            print(f"Rewriting '{edits.filepath}' with the AI generated solution...")
            with open(edits.filepath, "w") as f:
                f.write(edits.fixed_code)
        fix_applied = True
        retry_count += 1
    print(f"[-] Failed to fix '{target_dir}' after {max_retries + 1} attempts.")
    return False, fix_applied


if __name__ == "__main__":
    terraform_directories = find_tf_files()
    print(f"Found Terraform configurations in: {terraform_directories}")
    fix_applied = False
    all_directories_passed = True
    latest_explanation = ""
    fixed_successfully = False
    for tf_dir in terraform_directories:
        success, fixed = patch_dir(tf_dir)
        if fixed:
            fix_applied = True
        if success:
            fixed_successfully = True
        if not success:
            all_directories_passed = False
            latest_explanation = f"Failed to fix Terraform configuration in '{tf_dir}'."
            break     
    if fixed_successfully and all_directories_passed:
        print("Terraform configuration has been fixed successfully.")
        commit_message = "Automated multi-directory fix applied to Terraform configuration."
        print(subprocess.run(["git", "status"], capture_output=True, text=True).stdout)
        subprocess.run(["git", "add", "*.tf"])
        subprocess.run(["git", "commit", "-m", commit_message])
        print("Changes have been committed to the repository.")
    elif not all_directories_passed:
        print(latest_explanation)
        print("Please review the changes and fix any remaining issues manually.")
        if fix_applied:
            print(subprocess.run(["git", "status"], capture_output=True, text=True).stdout)
            subprocess.run(["git", "add", "*.tf"])
            subprocess.run(["git", "commit", "-m", "Automated partial fix applied to Terraform configurations."])
