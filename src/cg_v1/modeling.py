# modeling.py

import openai

problem_statement_function = [
    {
        "name": "problem_statement_function",
        "description": """This function is designed to isolate and describe a singular, primary issue with a product being sold on Amazon, using the data from customer complaints and the product's description.
        Example Output:     
            "problem_identification": "Lack of durability and insufficient planting space",
            "problem_statement": "The garden beds are perceived as flimsy and require additional support. They also appear to provide less planting space than customers expected.",
            "customer_voice_examples": [
                "The garden beds are flimsy and require additional support with wood framing.", 
                "Wished for more room for additional grow beds", 
                "Oval-shaped box loses a little planting space, but not worried about it at this time"
                ]""",
        "parameters": {
            "type": "object",
            "properties": {
                "problem_identification": {
                    "type": "string",
                    "description": "From the given data, identify and articulate the key problem or issue with the product." 
                },
                "problem_statement": {
                    "type": "string",
                    "description": "Elaborate on the identified problem, providing a detailed statement based on the observations made. This should be within a range of 200 words." 
                },
                "customer_voice_examples": {
                    "type": "string",
                    "description": "Select and provide quotes from customer complaints which further detail the problem and illustrate its impact. This should be up to 10 examples and within a range of 10 - 200 words." 
                },
            },
            "required": ["problem_identification", "problem_statement", "customer_voice_examples"]
        }
    }
]

def define_problem_statement(product_summary, issues):
    """Use GPT-3 to generate problem statement"""

    customer_voice_examples = issues[list(issues.keys())[0]][:10] # take first 10 examples

    prompt = f"Product Summary: {product_summary}\nIssues: {issues}\nExamples: {customer_voice_examples}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.7,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    content = response["choices"][0]["text"]

    return content


product_improvement_function = [
    {
        "name": "product_improvement_function",
        "description": """This function is designed to provide engineering solutions to address the primary issues with a product. The function uses the data from customer complaints and the product's description to propose technical product improvements. The Implementation Details  should be concise, yet comprehensive, explaining the rationale behind the solution and step-by-step instructions for carrying out the implementation. It should not contain jargon or technical terms that are not commonly understood by engineers in the relevant field.""",
        "parameters": {
            "type": "object",
            "properties": {
                "Product Improvement 1": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the first proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the first improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 2": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the second proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the second improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 3": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the third proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "AA detailed, 200-word description of the third improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 4": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fourth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fourth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 5": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fifth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fifth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 6": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the sixth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the sixth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 7": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the seventh proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the seventh improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
            },
            "required": ["Product Improvement 1", "Product Improvement 2", "Product Improvement 3", "Product Improvement 4", "Product Improvement 5", "Product Improvement 6", "Product Improvement 7"]
        }
    }
]

def generate_solutions(problem_statement, prepared_data, product_summary):
    
    prompt = f"Problem Statement: {problem_statement}\nProduct Summary: {product_summary}\nPrepared Data: {prepared_data}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.7,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=1
    )

    content = response["choices"][0]["text"]

    return content