from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InfrastructurePlan(BaseModel):
    aws_terraform: str
    azure_terraform: str

class CostComparison(BaseModel):
    analysis: str

def generate_terraform_plans(prompt: str, model="gpt-4o") -> InfrastructurePlan:
    system_prompt = """You are an expert in infrastructure as code. Given a description of infrastructure needs, 
    generate two separate Terraform configurations - one for AWS and one for Azure. 
    Return only the Terraform code without any explanations. The code should be valid and deployable."""
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format=InfrastructurePlan
    )
    return completion.choices[0].message.parsed

def run_infracost(terraform_dir: str) -> str:
    try:
        result = subprocess.run(
            ['infracost', 'breakdown', '--path', terraform_dir, '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running infracost: {str(e)}"

def compare_costs(initial_prompt: str, aws_cost: str, azure_cost: str, model="gpt-4o") -> CostComparison:
    system_prompt = """You are a cloud cost analysis expert. Compare the infrastructure costs between AWS and Azure.
    Provide insights about cost differences based on the cost analysis.
    Consider factors like pricing models, reserved instances, and potential long-term savings."""
    
    prompt = f"""
    Initial Prompt:
    {initial_prompt}
    
    AWS Cost Analysis:
    {aws_cost}
    
    Azure Cost Analysis:
    {azure_cost}
    
    Please provide a detailed comparison and recommendation.
    """
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format=CostComparison
    )
    return completion.choices[0].message.parsed

def synthetize(prompt: str, model="gpt-4o-mini") -> str:
    system_prompt = """You are an expert in infrastructure as code. Given a description of infrastructure code OR cost analysis, 
    generate a very concise report to help the user understand what being described."""
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()