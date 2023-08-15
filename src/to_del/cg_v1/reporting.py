# reporting.py

from fpdf import FPDF
import openai

def generate_report_content(solutions, problem_statement, issues, product_summary):
    """Use GPT-3 to generate full report content."""
    
    prompt = (f"Generate a full report based on the following: \n\n"
              f"Problem Statement: {problem_statement}\n\n"
              f"Solutions: {solutions}\n\n"
              f"Issues: {issues}\n\n"
              f"Product Summary: {product_summary}")

    try:
        response = openai.Completion.create(   
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.7,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Human:", "AI:"]
        )
        content = response["choices"][0]["text"]
        return content
    except Exception as e:
        print(f"Error generating report content: {e}")
        return None

def create_pdf_report(text, filename):
    """Generate PDF report from text content and save to a specified filename."""
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12) 

    for line in text.split("\n"):
        pdf.multi_cell(0, 5, line)

    pdf.output(filename) 

def export_report(report_text, filename="report.pdf"):
    """Generate and save PDF report."""
    
    if report_text:
        create_pdf_report(report_text, filename)
        print(f"Report exported to {filename}")
    else:
        print("Failed to generate report.")

