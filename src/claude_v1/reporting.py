# reporting.py

from fpdf import FPDF
import openai

def generate_report(solutions, problem_statement, issues, product_summary):
    """Use GPT-3 to generate full report content"""

    prompt = f"Generate a full report based on the following: \n\nProblem Statement: {problem_statement}\n\nSolutions: {solutions}\n\nIssues: {issues}\n\nProduct Summary: {product_summary}"

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

def create_pdf_report(text):
    """Generate PDF report from text content"""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12) 

    for line in text.split("\n"):
        pdf.multi_cell(0, 5, line)

    pdf.output("report.pdf") 

def export_report(report_text, filename="report.pdf"):
    """Generate and save PDF report"""

    create_pdf_report(report_text)

    print(f"Report exported to {filename}")