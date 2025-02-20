import streamlit as st
import json
from llm import generate_terraform_plans, run_infracost, compare_costs, synthetize
import os
import uuid

def create_output_button(label, key, is_enabled=False):
    # Custom CSS for the button
    st.markdown("""
        <style>
        div[data-testid="stButton"] button {
            width: 100%;
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #e0e3e9;
            margin: 2px 0;
            text-align: left;
            font-size: 0.9em;
            line-height: 1.2;
        }
        div[data-testid="stButton"] button:disabled {
            background-color: #e0e3e9;
            color: #8e9aab;
        }
        div[data-testid="stButton"] button:hover:enabled {
            background-color: #e0e3e9;
            border-color: #c0c3c9;
        }
        </style>
    """, unsafe_allow_html=True)
    return st.button(label, key=key, disabled=not is_enabled)

def create_shadow_container(content, content_type="text"):
    with st.container():
        st.markdown("""
            <style>
            .shadow-container {
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: white;
                margin: 15px 0;
                border: 1px solid #e0e3e9;
            }
            </style>
            """, unsafe_allow_html=True)
        
        with st.markdown('<div class="shadow-container">', unsafe_allow_html=True):
            if content_type == "code":
                st.code(content, language="hcl")
            else:
                st.write(content)
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Add custom CSS for better spacing and layout
    st.markdown("""
        <style>
        .main-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .stTitle {
            margin-bottom: 30px;
        }
        .section-header {
            margin: 12px 0 4px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #e0e3e9;
            font-size: 0.85em;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .generation-area {
            margin-bottom: 20px;
        }
        .content-area {
            margin-top: 20px;
        }
        /* Reduce spacing in sidebar */
        section[data-testid="stSidebar"] {
            padding-top: 1rem;
        }
        section[data-testid="stSidebar"] > div {
            padding-top: 1rem;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        /* Adjust markdown spacing in sidebar */
        section[data-testid="stSidebar"] h3 {
            margin: 0 0 8px 0;
        }
        section[data-testid="stSidebar"] p {
            margin: 0;
            padding: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session states
    if 'outputs' not in st.session_state:
        st.session_state.outputs = {
            'aws_terraform': None,
            'azure_terraform': None,
            'aws_synthesis': None,
            'azure_synthesis': None,
            'aws_cost': None,
            'azure_cost': None,
            'aws_cost_synthesis': None,
            'azure_cost_synthesis': None,
            'final_synthesis': None
        }
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = None
    if 'generation_state' not in st.session_state:
        st.session_state.generation_state = None
    if 'request_id' not in st.session_state:
        st.session_state.request_id = None
    if 'prompt' not in st.session_state:
        st.session_state.prompt = None

    # Main Content Area
    st.title("Cloud Infrastructure Cost Comparison")
    st.write("Describe your infrastructure needs and get a cost comparison between AWS and Azure")
    
    # Create a container for the input section
    with st.container():
        prompt = st.text_area("Describe your infrastructure needs:", height=150, key="input_prompt")
        generate_button = st.button("Generate Comparison", type="primary")
        
        if generate_button and prompt:
            # Store the prompt in session state
            st.session_state.prompt = prompt
            st.session_state.generation_state = 'started'
            st.session_state.request_id = str(uuid.uuid4())
            st.rerun()

    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### Navigation")
        
        # AWS Section
        st.markdown('<p class="section-header">AWS Resources</p>', unsafe_allow_html=True)
        if create_output_button("📋 Infrastructure Plan", "aws_tf_btn", 
                            st.session_state.outputs['aws_terraform'] is not None):
            st.session_state.active_tab = "aws_terraform"
            st.rerun()
        if create_output_button("🔍 Analysis", "aws_analysis_btn", 
                            st.session_state.outputs['aws_synthesis'] is not None):
            st.session_state.active_tab = "aws_synthesis"
            st.rerun()
        if create_output_button("💰 Cost Details", "aws_cost_btn", 
                            st.session_state.outputs['aws_cost_synthesis'] is not None):
            st.session_state.active_tab = "aws_cost"
            st.rerun()

        # Azure Section
        st.markdown('<p class="section-header">Azure Resources</p>', unsafe_allow_html=True)
        if create_output_button("📋 Infrastructure Plan", "azure_tf_btn", 
                            st.session_state.outputs['azure_terraform'] is not None):
            st.session_state.active_tab = "azure_terraform"
            st.rerun()
        if create_output_button("🔍 Analysis", "azure_analysis_btn", 
                            st.session_state.outputs['azure_synthesis'] is not None):
            st.session_state.active_tab = "azure_synthesis"
            st.rerun()
        if create_output_button("💰 Cost Details", "azure_cost_btn", 
                            st.session_state.outputs['azure_cost_synthesis'] is not None):
            st.session_state.active_tab = "azure_cost"
            st.rerun()

        # Summary Section
        st.markdown('<p class="section-header">Summary</p>', unsafe_allow_html=True)
        if create_output_button("📊 Cost Comparison", "cost_summary_btn", 
                            st.session_state.outputs['aws_cost_synthesis'] is not None and 
                            st.session_state.outputs['azure_cost_synthesis'] is not None):
            st.session_state.active_tab = "cost_summary"
            st.rerun()
        if create_output_button("📑 Final Analysis", "final_analysis_btn", 
                            st.session_state.outputs['final_synthesis'] is not None):
            st.session_state.active_tab = "final_analysis"
            st.rerun()

    # Generation Process Area
    generation_container = st.container()
    with generation_container:
        st.markdown('<div class="generation-area">', unsafe_allow_html=True)
        
        # Process generation states
        if st.session_state.generation_state == 'started':
            with st.spinner("Generating Terraform plans..."):
                plans = generate_terraform_plans(st.session_state.prompt)
                st.session_state.outputs['aws_terraform'] = plans.aws_terraform
                st.session_state.outputs['azure_terraform'] = plans.azure_terraform
                
                aws_dir = f"terraform_plans/aws_{st.session_state.request_id}"
                azure_dir = f"terraform_plans/azure_{st.session_state.request_id}"
                
                os.makedirs(aws_dir, exist_ok=True)
                os.makedirs(azure_dir, exist_ok=True)
                with open(f"{aws_dir}/main.tf", "w") as f:
                    f.write(plans.aws_terraform)
                with open(f"{azure_dir}/main.tf", "w") as f:
                    f.write(plans.azure_terraform)
                
                st.session_state.generation_state = 'terraform_done'
                st.rerun()
        
        elif st.session_state.generation_state == 'terraform_done':
            with st.spinner("Analyzing infrastructure..."):
                st.session_state.outputs['aws_synthesis'] = synthetize(st.session_state.outputs['aws_terraform'])
                st.session_state.outputs['azure_synthesis'] = synthetize(st.session_state.outputs['azure_terraform'])
                st.session_state.generation_state = 'analysis_done'
                st.rerun()
        
        elif st.session_state.generation_state == 'analysis_done':
            with st.spinner("Running cost analysis..."):
                aws_dir = f"terraform_plans/aws_{st.session_state.request_id}"
                azure_dir = f"terraform_plans/azure_{st.session_state.request_id}"
                st.session_state.outputs['aws_cost'] = run_infracost(aws_dir)
                st.session_state.outputs['azure_cost'] = run_infracost(azure_dir)
                st.session_state.outputs['aws_cost_synthesis'] = synthetize(st.session_state.outputs['aws_cost'])
                st.session_state.outputs['azure_cost_synthesis'] = synthetize(st.session_state.outputs['azure_cost'])
                st.session_state.generation_state = 'cost_done'
                st.rerun()
        
        elif st.session_state.generation_state == 'cost_done':
            with st.spinner("Generating final analysis..."):
                comparison = compare_costs(st.session_state.prompt, st.session_state.outputs['aws_cost'], 
                                        st.session_state.outputs['azure_cost'])
                st.session_state.outputs['final_synthesis'] = synthetize(comparison.analysis)
                st.session_state.generation_state = 'complete'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Content Display Area
    content_container = st.container()
    with content_container:
        st.markdown('<div class="content-area">', unsafe_allow_html=True)
        if st.session_state.active_tab:
            if st.session_state.active_tab == "aws_terraform":
                st.subheader("AWS Infrastructure Plan")
                create_shadow_container(st.session_state.outputs['aws_terraform'], "code")
            elif st.session_state.active_tab == "aws_synthesis":
                st.subheader("AWS Infrastructure Analysis")
                create_shadow_container(st.session_state.outputs['aws_synthesis'])
            elif st.session_state.active_tab == "aws_cost":
                st.subheader("AWS Cost Analysis")
                create_shadow_container(st.session_state.outputs['aws_cost_synthesis'])
            elif st.session_state.active_tab == "azure_terraform":
                st.subheader("Azure Infrastructure Plan")
                create_shadow_container(st.session_state.outputs['azure_terraform'], "code")
            elif st.session_state.active_tab == "azure_synthesis":
                st.subheader("Azure Infrastructure Analysis")
                create_shadow_container(st.session_state.outputs['azure_synthesis'])
            elif st.session_state.active_tab == "azure_cost":
                st.subheader("Azure Cost Analysis")
                create_shadow_container(st.session_state.outputs['azure_cost_synthesis'])
            elif st.session_state.active_tab == "cost_summary":
                st.subheader("Cost Comparison Summary")
                create_shadow_container(f"""
                **AWS Cost Analysis**: {st.session_state.outputs['aws_cost_synthesis']}
                
                **Azure Cost Analysis**: {st.session_state.outputs['azure_cost_synthesis']}
                """)
            elif st.session_state.active_tab == "final_analysis":
                st.subheader("Final Analysis")
                create_shadow_container(st.session_state.outputs['final_synthesis'])
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
