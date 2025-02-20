import streamlit as st
import json
from llm import generate_terraform_plans, run_infracost, compare_costs, synthetize
import os
import uuid

def main():
    # Move navigation to sidebar
    with st.sidebar:
        st.markdown("### Quick Navigation")
        st.markdown("""
            - [Infrastructure Summary](#infrastructure-summary)
            - [Cost Summary](#cost-summary)
            - [Final Analysis](#final-analysis)
        """)
        # Add some spacing and a divider
        st.markdown("---")
    
    st.title("Cloud Infrastructure Cost Comparison")
    st.write("Describe your infrastructure needs and get a cost comparison between AWS and Azure")
    
    prompt = st.text_area("Describe your infrastructure needs:", height=200)
    
    if st.button("Generate Comparison"):
        if prompt:
            # Create a container at the bottom of the page for the final synthesis
            final_container = st.container()

            summary_container = st.container()
            
            with st.spinner("Generating Terraform plans..."):
                plans = generate_terraform_plans(prompt)
            
            # Generate a unique ID for this request
            request_id = str(uuid.uuid4())
            aws_dir = f"terraform_plans/aws_{request_id}"
            azure_dir = f"terraform_plans/azure_{request_id}"
            
            # Create directories and write files
            os.makedirs(aws_dir, exist_ok=True)
            os.makedirs(azure_dir, exist_ok=True)
            # Write the Terraform plans to files
            with open(f"{aws_dir}/main.tf", "w") as f:
                f.write(plans.aws_terraform)
            with open(f"{azure_dir}/main.tf", "w") as f:
                f.write(plans.azure_terraform)
                
            # Display the Terraform plans in collapsible sections
            with st.expander("View AWS Terraform Plan"):
                st.code(plans.aws_terraform, language="hcl")
            with st.expander("View Azure Terraform Plan"):
                st.code(plans.azure_terraform, language="hcl")
            
            with st.spinner("Analyzing AWS infrastructure..."):
                aws_synthesis = synthetize(plans.aws_terraform)
            with st.spinner("Analyzing Azure infrastructure..."):
                azure_synthesis = synthetize(plans.azure_terraform)

            # Display terraform synthesis first
            st.markdown("## Infrastructure Summary")
            with st.expander("View AWS Terraform synthesis"):
                st.write(f"**AWS Plan**: {aws_synthesis}")
            with st.expander("View Azure Terraform synthesis"):
                st.write(f"**Azure Plan**: {azure_synthesis}")
            
            with st.spinner("Running AWS cost analysis..."):
                aws_cost = run_infracost(aws_dir)
            with st.spinner("Running Azure cost analysis..."):
                azure_cost = run_infracost(azure_dir)
            
            # Cost synthesis displayed
            with st.spinner("Analyzing AWS costs..."):
                aws_cost_synthesis = synthetize(aws_cost)
            with st.spinner("Analyzing Azure costs..."):
                azure_cost_synthesis = synthetize(azure_cost)
                
            with summary_container:
                st.markdown("## Cost Summary")
                st.write(f"**AWS Cost Analysis**: {aws_cost_synthesis}")
                st.write(f"**Azure Cost Analysis**: {azure_cost_synthesis}")
            
            with st.spinner("Generating final cost comparison..."):
                comparison = compare_costs(prompt, aws_cost, azure_cost)
    
            with st.spinner("Analyzing final cost comparison..."):
                final_synthesis = synthetize(comparison.analysis)
            
            # Use the container created earlier to display the final synthesis at the bottom
            with final_container:
                st.markdown("## Final Analysis")
                st.write(final_synthesis)
        else:
            st.error("Please provide a description of your infrastructure needs.")

if __name__ == "__main__":
    main()
