# Importing dependencies
import os
import time
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv


# Setting up the API key for single project
# 1/ create a .env file and add to it:
# OPENAI_API_KEY = "sk-proj-..."
# 2/ load variables from .env file
load_dotenv()
# 3/ set up the client 
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


# Defining the PromptEnhancer class containing the necessary components for the Advanced Prompt Generation Pipeline
class PromptEnhancer:
    def __init__(self, model="gpt-4o-mini", tools_dict={}):
        self.model = model
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tools_dict = tools_dict


    async def call_llm(self, prompt):
        """Call the LLM with the given prompt"""
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", 
                 "content": 
                     "You are a highly intelligent AI assistant. Your task is to analyze, and comprehend the provided prompt,\
                        then provide clear, and concise response based strictly on the given instructions.\
                        Do not include any additional explanations or context beyond the required output."
                 },
                {"role": "user", 
                 "content": prompt
                 } 
                ],
            temperature=0.0, # from 0 (precise and almost deterministic answer) to 2 (creative and almost random answer)
        )
        # counting the I/O tokens
        self.prompt_tokens += response.usage.prompt_tokens
        self.completion_tokens += response.usage.completion_tokens

        return response.choices[0].message.content


    async def analyze_and_expand_input(self, input_prompt):
        analysis_and_expansion_prompt = f"""
        You are a highly intelligent assistant. 
        Analyze the provided {{prompt}} and generate concise answers for the following key aspects:

        - **Main goal of the prompt:** Identify the core subject or request within the provided prompt.
        - **Persona:** Recommend the most relevant persona for the AI model to adopt (e.g., expert, teacher, conversational, etc.)
        - **Optimal output length:** Suggest an optimal output length (short, brief, medium, long) based on the task, and give an approximate number of words if it is suitable for the case.
        - **Most convenient output format:** Recommend the optimal format for the result (e.g., list, paragraph, code snippet, table, JSON, etc.).
        - **Specific requirements:** Highlight any special conditions, rules, or expectations stated or implied within the prompt.
        - **Suggested improvements:** Offer recommendations on how to modify or enhance the prompt for more precise or efficient output generation.
        - **One-shot prompting:** Create one related examples to guide the output generation.
        
        Then use them to reformulate and expand the provided {{prompt}}.
        Return the expanded prompt as output in text format. Refrain from explaining the generation process.

        Example 1:
        {{prompt}}: "Explain quantum entanglement to a 10-year-old."
        
        *thought_process*:
        - **Main goal of the prompt:** Simplify complex quantum physics concept for children.
        - **Persona:** Patient, friendly teacher
        - **Optimal output length:** Brief (100-150 words)
        - **Most convenient output format:** Narrative with analogy
        - **Specific requirements:** Age-appropriate explanation (10-year-old).
        - **Suggested improvements:** 
            - Request specific analogies
            - Include interactive elements
            - Add follow-up questions
            - Suggest visual aids
        - **One-shot prompting:**
        Output example:
            "Imagine you have two special pairs of socks. When you put one sock in your room and the other sock in the kitchen, 
            something magical happens! Whatever happens to one sock instantly affects the other sock. 
            If you turn one sock inside out, the other sock automatically turns inside out too, no matter how far apart they are!" 
        
        *output*:
        As a friendly science teacher, please explain quantum entanglement to a 10-year-old student using these guidelines:

        Start with a relatable analogy using everyday objects
        Use simple, clear language avoiding technical terms
        Include 2-3 interactive examples that demonstrate the concept
        Add fun facts that will spark curiosity
        End with simple questions to check understanding
        Keep the explanation brief (100-150 words)

        Structure your explanation as:
        
        Opening analogy
        Main explanation with examples
        Interactive "What if?" scenarios
        Fun facts about quantum entanglement
        Check-for-understanding questions

        Remember to maintain an enthusiastic and encouraging tone throughout the explanation.
        
        Output example:
        Imagine you have two special pairs of socks. When you put one sock in your room and the other sock in the kitchen, 
        something magical happens! Whatever happens to one sock instantly affects the other sock. 
        If you turn one sock inside out, the other sock automatically turns inside out too, no matter how far apart they are!

        Example 2:
        {{prompt}}: "Write a function to calculate the Fibonacci sequence up to n terms."
        
        *thought_process*:
        - **Main goal of the prompt:** Create a programming function that generates Fibonacci numbers
        - **Persona:** Programming expert
        - **Optimal output length:** Medium (150-200 words including code)
        - **Most convenient output format:** Code snippet with explanatory comments
        - **Specific requirements:** Function must accept parameter n for sequence length
        - **Suggested improvements:** 
            - Specify programming language
            - Clarify if 0 should be included as first term
            - Define expected handling of negative inputs
        - **One-shot prompting:** 
        
        *output*:
        As an expert programmer, please create a well-documented function to generate the Fibonacci sequence. 
        
        Requirements:
        Accept a parameter 'n' specifying the number of terms to generate
        Handle edge cases (n <= 0, n == 1)
        Return the sequence as a list/array
        Include proper error handling
        Add comments explaining the logic

        Provide the implementation in Python, including:
        Function definition with docstring
        Input validation
        Core algorithm
        Example usage with outputs for n=5, n=1, and n=0

        For reference, the sequence should start with [0, 1, ...] where each subsequent number is the sum of the previous two numbers.
        
        
        Now, analyze the following prompt then return only the generated *output*:
        {{prompt}}: {input_prompt}
        """

        return await self.call_llm(analysis_and_expansion_prompt)

    
    async def decompose_and_add_reasoning(self, expanded_prompt):
        decomposition_and_reasoning_prompt = f"""
        You are a highly capable AI assistant tasked with improving complex task execution. 
        Analyze the provided {{prompt}}, and use it to generate the following output:
        
        - **Subtasks decomposition:** Break down the task described in the prompt into manageable and specific subtasks that the AI model needs to address.
        - **Chain-of-thought reasoning:** For subtasks that involve critical thinking or complex steps, add reasoning using a step-by-step approach to improve decision-making and output quality.
        - **Success criteria:** Define what constitutes a successful completion for each subtask, ensuring clear guidance for expected results.

        Return the following structured output for each subtask:

        1. **Subtask description**: Describe a specific subtask.
        2. **Reasoning**: Provide reasoning or explanation for why this subtask is essential or how it should be approached.
        3. **Success criteria**: Define what successful completion looks like for this subtask.

        Example 1:
        {{Prompt}}: "Explain how machine learning models are evaluated using cross-validation."

        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: Define cross-validation and its purpose.
        - **Reasoning**: Clarifying the concept ensures the reader understands the basic mechanism behind model evaluation.
        - **Success criteria**: The explanation should include a clear definition of cross-validation and its role in assessing model performance.
        *Subtask 2*:
        - **Description**: Describe how cross-validation splits data into training and validation sets.
        - **Reasoning**: Explaining the split is crucial to understanding how models are validated and tested for generalization.
        - **Success criteria**: A proper explanation of k-fold cross-validation with an illustration of how data is split.
        *Subtask 3*:
        - **Description**: Discuss how cross-validation results are averaged to provide a final evaluation metric.
        - **Reasoning**: Averaging results helps mitigate the variance in performance due to different training/validation splits.
        - **Success criteria**: The output should clearly explain how the final model evaluation is derived from multiple iterations of cross-validation.

        Example 2:
        {{Prompt}}: "Write a function to calculate the factorial of a number."

        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: Define what a factorial is.
        - **Reasoning**: Starting with a definition ensures the user understands the mathematical operation required.
        - **Success criteria**: Provide a concise definition with an example (e.g., 5! = 5 x 4 x 3 x 2 x 1 = 120).
        *Subtask 2*:
        - **Description**: Write the base case for the factorial function.
        - **Reasoning**: In recursive programming, defining a base case is essential to avoid infinite recursion.
        - **Success criteria**: Include a clear base case, such as `n = 1`, to ensure termination of recursion.
        *Subtask 3*:
        - **Description**: Implement the recursive step for the factorial function.
        - **Reasoning**: The recursive case should reflect the mathematical definition of factorial.
        - **Success criteria**: The function should return `n * factorial(n-1)` for positive integers.
        
        Example 3:
        {{Prompt}}: "Explain the process of photosynthesis in plants."

        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: Define photosynthesis and its overall purpose in plants.
        - **Reasoning**: Starting with a definition provides context and sets the stage for a detailed explanation.
        - **Success criteria**: Clear and concise definition of photosynthesis, mentioning its role in converting sunlight into chemical energy.
        *Subtask 2*:
        - **Description**: Break down the steps involved in the photosynthesis process (e.g., light-dependent and light-independent reactions).
        - **Reasoning**: Understanding the individual steps helps to grasp the complexity of how plants convert light into usable energy.
        - **Success criteria**: Explain both the light-dependent reactions (e.g., capturing light energy) and the Calvin cycle (sugar formation).
        *Subtask 3*:
        - **Description**: Discuss the importance of photosynthesis to the ecosystem and human life.
        - **Reasoning**: Highlighting the broader implications reinforces the significance of this process beyond the biological aspect.
        - **Success criteria**: Provide examples of how photosynthesis contributes to oxygen production and energy flow in ecosystems.

        Example 4:
        {{Prompt}}: "Design a user-friendly login interface for a mobile app."

        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: Identify key user interface elements (e.g., username field, password field, login button).
        - **Reasoning**: Identifying these core elements ensures the interface includes the necessary components for functionality.
        - **Success criteria**: The interface should include a username input, password input, and a clearly labeled login button.
        *Subtask 2*:
        - **Description**: Focus on the user experience, ensuring simplicity and intuitive navigation.
        - **Reasoning**: An intuitive design ensures a seamless user experience, reducing friction for users during the login process.
        - **Success criteria**: The layout should be minimalistic with clear labels, making the login process simple and quick.
        *Subtask 3*:
        - **Description**: Implement security features like password masking and error handling for incorrect logins.
        - **Reasoning**: Security measures ensure that user data is protected and help guide users when errors occur.
        - **Success criteria**: Passwords should be masked by default, and error messages should be informative but secure (e.g., "Incorrect username or password").

        Example 5:
        {{Prompt}}: "Outline the steps to bake a chocolate cake from scratch."

        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: List all the ingredients required for the cake.
        - **Reasoning**: Starting with ingredients ensures all necessary components are prepared before beginning the process.
        - **Success criteria**: Provide a complete list of ingredients, including measurements (e.g., 2 cups of flour, 1 cup of sugar, etc.).
        *Subtask 2*:
        - **Description**: Describe the preparation steps, such as mixing dry and wet ingredients.
        - **Reasoning**: Detailing the preparation steps ensures that the user follows the correct sequence for combining ingredients.
        - **Success criteria**: Instructions should specify when and how to mix ingredients to achieve the right consistency.
        *Subtask 3*:
        - **Description**: Explain the baking time and temperature.
        - **Reasoning**: Providing accurate baking instructions is crucial for the cake to cook properly.
        - **Success criteria**: Specify an appropriate baking temperature (e.g., 350°F) and time (e.g., 25-30 minutes), along with how to check for doneness.

        Example 6:
        {{Prompt}}: "Create a marketing plan for a new eco-friendly product."
        
        ##THOUGHT PROCESS##
        *Subtask 1*:
        - **Description**: Identify the target audience for the eco-friendly product.
        - **Reasoning**: Defining the target audience is essential for tailoring the marketing message and strategy effectively.
        - **Success criteria**: Provide a detailed description of the ideal customer demographics and psychographics (e.g., age, values, eco-consciousness).
        *Subtask 2*:
        - **Description**: Outline the key messaging and brand positioning.
        - **Reasoning**: Clear messaging ensures the product’s benefits and unique selling points are communicated effectively to the target audience.
        - **Success criteria**: Develop a compelling message that highlights the eco-friendliness, sustainability, and benefits of the product.
        *Subtask 3*:
        - **Description**: Define the marketing channels to be used (e.g., social media, email campaigns, influencer partnerships).
        - **Reasoning**: Selecting the appropriate channels ensures that the marketing plan reaches the right audience in an impactful way.
        - **Success criteria**: Choose a mix of channels based on the target audience’s preferences and behaviors, including both digital and traditional media.
        

        Now, analyze the following expanded prompt and return the subtasks, reasoning, and success criteria.
        Prompt: {expanded_prompt}
        """
        return await self.call_llm(decomposition_and_reasoning_prompt)

    
    
    async def suggest_enhancements(self, input_prompt, tools_dict={}):
        enhancement_suggestion_prompt = f"""
        You are a highly intelligent assistant specialized in reference suggestion and tool integration.
        Analyze the provided {{input_prompt}} and the available {{tools_dict}} to recommend enhancements:

        - **Reference necessity:** Determine if additional reference materials would benefit the task execution (e.g., websites, documentations, books, articles, etc.)
        - **Tool applicability:** Evaluate if any available tools could enhance efficiency or accuracy
        - **Integration complexity:** Assess the effort required to incorporate suggested resources
        - **Expected impact:** Estimate the potential improvement in output quality
        
        If enhancements are warranted, provide structured recommendations in this format:
        
        ##REFERENCE SUGGESTIONS##
        (Only if applicable, maximum 3)
        - Reference name/type
        - Purpose: How it enhances the output
        - Integration: How to incorporate it
        
        ##TOOL SUGGESTIONS##
        (Only if applicable, maximum 3)
        - Tool name from tools_dict
        - Purpose: How it improves the task
        - Integration: How to implement it
        
        If no enhancements would significantly improve the output, return an empty string ""

        Example 1:
        {{input_prompt}}: "Write a Python function to detect faces in images using computer vision."
        {{tools_dict}}: {{}}
        *output*:
        ##REFERENCE SUGGESTIONS##
        - OpenCV Face Detection Documentation
          Purpose: Provides implementation details and best practices
          Integration: Reference for optimal parameter settings and cascade classifier usage        
        
        Example 2:
        {{input_prompt}}: "Write a haiku about spring."
        {{tools_dict}}: {{"textblob": "Text processing library", "gpt": "Language model"}}
        *output*:
        
        
        Example 3:
        {{expanded_prompt}}: "Create a sentiment analysis function for customer reviews."
        {{tools_dict}}: {{}}
        *output*:
        ##REFERENCE SUGGESTIONS##
        - VADER Sentiment Analysis Paper
          Purpose: Provides insights into social media text sentiment analysis
          Integration: Reference for understanding compound sentiment scoring
        
        Example 4:
        {{expanded_prompt}}: "Generate a weather forecast report for New York."
        {{tools_dict}}: {{"requests": "HTTP library", "json": "JSON parser", "weather_api": "Weather data service"}}
        *output*:
        ##TOOL SUGGESTIONS##
        - weather_api
          Purpose: Provides real-time weather data
          Integration: Use API endpoints for forecast data retrieval
        - requests
          Purpose: Make HTTP requests to weather API
          Integration: Use requests.get() to fetch weather data
        
        Example 5:
        {{expanded_prompt}}: "Calculate the factorial of a number."
        {{tools_dict}}: {{}}
        *output*:
        

        Example 6:
        {{expanded_prompt}}: "Create an API endpoint documentation."
        {{tools_dict}}: {{"swagger": "API documentation tool", "markdown": "Text formatting", "json_schema": "JSON schema validator"}}
        *output*:
        ##REFERENCE SUGGESTIONS##
        - OpenAPI Specification
          Purpose: Provides standard API documentation format
          Integration: Use as template for documentation structure
        - REST API Best Practices
          Purpose: Ensures documentation follows industry standards
          Integration: Reference for endpoint description patterns
        
        ##TOOL SUGGESTIONS##
        - swagger
          Purpose: Generate interactive API documentation
          Integration: Use Swagger UI for visual documentation
        - json_schema
          Purpose: Validate API request/response schemas
          Integration: Define and validate data structures
          
        Example 7:
        {{expanded_prompt}}: "Create an API endpoint documentation."
        {{tools_dict}}: {{}}
        *output*:
        ##REFERENCE SUGGESTIONS##
        - OpenAPI Specification
          Purpose: Provides standard API documentation format
          Integration: Use as template for documentation structure
        - REST API Best Practices
          Purpose: Ensures documentation follows industry standards
          Integration: Reference for endpoint description patterns


        Now, analyze the following prompt and tools, then return only the generated *output*:
        {{input_prompt}}: {input_prompt}
        {{tools_dict}}: {tools_dict}
        """
        return await self.call_llm(enhancement_suggestion_prompt)
    
    
    async def assemble_prompt(self, components):
        expanded_prompt = components.get("expanded_prompt", "")
        decomposition_and_reasoninng = components.get("decomposition_and_reasoninng", "")
        suggested_enhancements = components.get("suggested_enhancements", "")
        
        output_prompt = (
            f"{expanded_prompt}\n\n"
            f"{suggested_enhancements}\n\n"
            f"{decomposition_and_reasoninng}"
        )
        return output_prompt
    
    
    async def enhance_prompt(self, input_prompt):
        
        # TODO: Add a function to update the tools_dict
        # TODO: Add function calling method
        
        tools_dict = {}
        
        expanded_prompt = await self.analyze_and_expand_input(input_prompt)
        suggested_enhancements = await self.suggest_enhancements(input_prompt, tools_dict)
        decomposition_and_reasoning = await self.decompose_and_add_reasoning(expanded_prompt)
        
        components = {
            "expanded_prompt":expanded_prompt,
            "decomposition_and_reasoninng": decomposition_and_reasoning,
            "suggested_enhancements": suggested_enhancements
        }
        
        output_prompt = await self.assemble_prompt(components)
        
        return output_prompt




async def main():
    print("-"*52)
    print("||||||||||| ADVANCED PROMPT GENERATOR |||||||||||")
    print("-"*52, "\n")
    
    print("|- Choose the model -----------------------------")
    print("|   1) GPT-4o")
    print("|   2) GPT-4o-mini")
    print("|")
    
    which_model = input("|   Select [1/2]: \n|   > ")
    
    if which_model == "1":
        model="gpt-4o"
        i_cost=5/10**6
        o_cost=15/10**6
    elif which_model == "2":
        model="gpt-4o-mini"
        i_cost=0.15/10**6
        o_cost=0.6/10**6
    else:
        raise Exception("Please input a valide choice")
    
    print("|")
    
    input_prompt = input("|- Enter your Prompt ---------------------------- \n|   > ")
    print("\n")

    # Add option to choose output format
    print("|- Choose output format -------------------------")
    print("|   1) Console")
    print("|   2) .txt file")
    print("|")
    
    output_choice = input("|   Select [1/2]: \n|   > ")
    print("|")
    
    enhancer = PromptEnhancer(model)
    
    print(f"SELECTED MODEL: GPT-{enhancer.model[4:]}\n")
    print("PROCESSING ... \n")
    
    start_time = time.time()
    
    advanced_prompt = await enhancer.enhance_prompt(input_prompt)
    
    elapsed_time = time.time() - start_time

    print("-"*52)
    print("\n--- RESULTS -------------------------------------")
    print(f"- Execution Time: {elapsed_time:.2f} seconds")
    print(f"- Prompt Tokens Count = {enhancer.prompt_tokens}")
    print(f"- Completion Tokens Count = {enhancer.completion_tokens}")
    print(f"- Approximate Cost = ${(enhancer.prompt_tokens*i_cost)+(enhancer.completion_tokens*o_cost)}\n")
    print("-"*52, "\n")
    
    if output_choice == "1":
        # Print output to console
        print(">>> BASIC PROMPT: \n")
        print(input_prompt, "\n")
        print("-"*52, "\n")
        print(">>> ADVANCED PROMPT: \n")
        print(advanced_prompt, "\n")
        print("-"*52, "\n")
    elif output_choice == "2":
        # Write output to a .txt file
        with open("output.txt", "w") as f:
            f.write("Basic Prompt:\n")
            f.write(input_prompt + "\n")
            f.write("-"*52 + "\n")
            f.write("Advanced Prompt:\n")
            f.write(advanced_prompt)
        print("Output saved to output.txt")
    else:
        raise Exception("Please input a valid choice")

    
if __name__ == "__main__":
    asyncio.run(main())
    