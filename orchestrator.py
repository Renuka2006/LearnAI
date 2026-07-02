import subprocess
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel


class TerraformFix(BaseModel):
    explanation: str
    fixed_code: str

def ask_gemini_to_fix(broken_code, error_logs):
    print("Sending the logs to Gemini for analysis and fix...")
    client = genai.Client()
    system_instruction = ("You are an expert Site Reliability Engineer and automated patching agent. "
                          "Your job is to analyze broken Terraform configurations and logs, determine the root cause, "
                          "and provide the corrected codebase. Do not provide conversational responses outside the requested schema.")
    user_prompt = f"""The following Terraform code is failing validation:
    ---
    {broken_code}
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
def terraform_init():
    print("Initializing Terraform...")
    result = subprocess.run(["terraform", "init"], capture_output=True, text=True)
    err_logs = result.stderr if result.stderr else result.stdout
    if result.returncode != 0:
        print("Terraform initialization failed. Please check the error messages below:")
        print(err_logs)
        exit(1)
    else:
        print("Terraform initialization completed successfully.")

def run_terraform_validation():
    print("Running Terraform validation...")

    result = subprocess.run(["terraform", "validate"], capture_output=True, text=True)
    #print(result.stderr,result.stdout)

    if result.returncode != 0:
        print("TF Validation has Failed. Please check the error messages below:")
        err_logs = result.stderr if result.stderr else result.stdout
        return False, err_logs

    print("TF Validation has Passed!!!")
    return True, None



if __name__ == "__main__":

    MAX_RETRIES = 3
    retry_count = 0
    fix_applied = False
    latest_explanation = ""
    fixed_successfully = False
    while retry_count <= MAX_RETRIES:
        try:
            with open("main.tf", "r") as f:
                code = f.read()
        except FileNotFoundError:
            print("Error: main.tf not found.")
            exit(1)
        success, logs = run_terraform_validation()
        if success:
            if retry_count == 0:
                print("Terraform configuration is valid. No fixes needed.")
            else:
                print("Terraform configuration is valid after applying the fix.")
            break

        #json_response = ask_gemini_to_fix(code, logs)
        data = ask_gemini_to_fix(code, logs)
        #print("\n--- AI RESPONSE CAPTURED---")
        print("Explanation of the Issue:")
        print("--------------------------------------------")
        print(data.explanation)
        print("--------------------------------------------")
        print("Suggested Code Fix:")
        print("--------------------------------------------")
        print(data.fixed_code)
        print("--------------------------------------------")
        print("Rewriting 'main.tf' with the AI generated solution...")
        with open("main.tf","w") as f:
            f.write(data.fixed_code)
        fix_applied = True
        fixed_successfully = True
        retry_count += 1
    if fix_applied and fixed_successfully:
        print("Terraform configuration has been fixed successfully.")
        commit_message = f"Automated fix applied to Terraform configuration."
        subprocess.run(["git", "add", "main.tf"])
        subprocess.run(["git", "commit", "-m", commit_message])
        print("Changes have been committed to the repository.")