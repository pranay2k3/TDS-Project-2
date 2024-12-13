import json
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import requests
import seaborn as sns
import openai


token = os.getenv("AIPROXY_TOKEN")
if not token:
    print("Error: AIPROXY_TOKEN environment variable is not set.")
    sys.exit(1) 


api_url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"


def load_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def perform_basic_analysis(df):
    analysis = {}
    analysis["shape"] = df.shape
    analysis["missing_values"] = df.isnull().sum().to_dict()
    analysis["data_types"] = df.dtypes.apply(str).to_dict()
    analysis["summary_statistics"] = df.describe(include='all').to_dict()
    numeric_columns = df.select_dtypes(include='number').columns
    if len(numeric_columns) > 1:
        numeric_df = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
        analysis["correlation_matrix"] = numeric_df.corr().to_dict()
    return analysis

def query_llm(prompt):
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    try:
        data = {
            "model":"gpt-4o-mini",
            "messages":[
                {"role": "system", "content": "You are a data analysis assistant."},
                {"role": "user", "content": prompt}
            ]
        }


        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
                    
                    story = response.json()['choices'][0]['message']['content'].strip()
                    print("Story generated.") 
                    return story
        else:
            print(f"Error with request: {response.status_code} - {response.text}")
            return "Failed to generate story."

    except Exception as e:
        print(f"Error: {e}")
        return "Failed to generate story."
    


def generate_visualizations(df, analysis):
    try:
       
        if "correlation_matrix" in analysis:
            plt.figure(figsize=(10, 8))
            sns.heatmap(pd.DataFrame(analysis["correlation_matrix"]), annot=True, fmt=".2f", cmap="coolwarm")
            plt.title("Correlation Heatmap")
            plt.savefig("correlation_heatmap.png")
            plt.close()

       
        missing_values = pd.Series(analysis["missing_values"])
        if missing_values.sum() > 0:
            plt.figure(figsize=(10, 6))
            missing_values.plot(kind="bar", color="skyblue")
            plt.title("Missing Values per Column")
            plt.ylabel("Count")
            plt.savefig("missing_values.png")
            plt.close()
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        sys.exit(1)

def create_readme( additional_insights, images):

    
    readme_content = f"""# Automated Data Analysis

    # Insights from LLM
    {additional_insights}

    # Visualizations
"""
    
    for img in images:
        readme_content += f"![{img}]({img})\n"

   
    with open("README.md", "w") as f:
        f.write(readme_content)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    data = load_dataset(csv_file)

    print("Performing basic analysis...")
    basic_analysis = perform_basic_analysis(data)

    print("Querying LLM for further analysis suggestions...")
    llm_prompt = f"""
    I have a dataset with the following details:
    
    Shape: {basic_analysis['shape']}
    Data Types: {basic_analysis['data_types']}
    Missing Values: {basic_analysis['missing_values']}
    Summary Statistics: {pd.DataFrame(basic_analysis['summary_statistics']).to_string()}
    structure the data i have given above and output it after that 
    Do Data analysis
    Based on the following data analysis, please generate a creative and engaging story. The story should include multiple paragraphs, a clear structure with an introduction, body, and conclusion, and should feel like a well-rounded narrative.
    The story should be elaborate and cover the following:
    -The data you received, briefly
    The analysis you carried out
    The insights you discovered
    The implications of your findings"""
    
    insights_from_llm = query_llm(llm_prompt)

    print("Generating visualizations...")
    generate_visualizations(data, basic_analysis)

    print("Creating README.md...")
    create_readme(insights_from_llm, ["correlation_heatmap.png", "missing_values.png"])
    
    print("Analysis complete.")
