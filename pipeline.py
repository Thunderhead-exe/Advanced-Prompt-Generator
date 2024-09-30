# Importing dependecies
import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv


# Setting up the API key for single project
# 1/ create a .env file and add to it:
# OPENAI_API_KEY = the_personal_api_key
# 2/ load variables from .env file
load_dotenv()
# 3/ set up the client 
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


# Defining the PromptEnhancer class containing the necessary components for the Advanced Prompt Generation Pipeline
class PromptEnhancer:
    def __init__(self, model="gpt-4o-mini", temperature=0.0, tools_dict={}):
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
                 "content": "You are an assistant designed to provide concise and specific information based solely on the given tasks.\
                     Do not include any additional information, explanations, or context beyond what is explicitly requested."
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

    async def analyze_input(self, basic_prompt):
        """Analyze the input prompt to determine its key information"""
        analysis_prompt = f"""
        Analyze the following {{prompt}} and generate brief answers to these key information that will be beneficial to enhance the prompt: 
        1. Main topic of the prompt 
        2. The most convenient output format for the prompt 
        3. Specific requirements for the prompt, if necessary
        4. Suggested strategies to enhance the prompt for better output result

        {{prompt}}: {basic_prompt}
        
        Your output will be only the result of the information required above in text format.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(analysis_prompt)

    async def expand_instructions(self, basic_prompt, analysis):
        """Expand the basic prompt with clear, detailed instructions"""
        expansion_prompt = f"""
        Based on this {{analysis}}: 
        
        {analysis}
        
        Expand the following {{basic_prompt}} following these instructions: 
        1. Add relevant details to clarify the prompt only if necessary
        2. Suggest an appropriate persona for the AI Model 
        3. Generate 1-2 related examples to guide the output generation 
        4. Suggest an optimal output length 
        5. Use delimiter, {{ }}, to clearly indicate the parts of the input that should be concidered as variables

        {{basic_prompt}}: {basic_prompt}
               
        Your output will be only the result of the information required above in text format and not a dictionary format.
        Make sure the generated output maintains the sructure of a prompt for an AI Model. 
        Make sure the generated output maintains the goal and context of the {{basic_prompt}}.
        Do not include the instructions headers in the generated answer. 
        Do not return a general explanation of the generation process.
        Do not generate an answer for the prompt. 
        """
        return await self.call_llm(expansion_prompt)

    async def decompose_task(self, expanded_prompt):
        """Break down complex tasks into subtasks"""
        decomposition_prompt = f"""
        Break down the following {{prompt}} into subtasks for better output generation and follow these instructions:
        1. Identify main task components and their corresponding subtasks
        2. Create specific instructions for each subtask
        3. Define success criteria for each subtask

        {{prompt}}: {expanded_prompt}
        
        Your output will be only the result of the task required above in text format.
        Follow the (Main-task/ Sub-task/ Instructions/ Success-criteria) format.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(decomposition_prompt)

    async def add_reasoning(self, expanded_prompt):
        """Add instructions for showing reasoning, chain-of-thought, and self-review"""
        reasoning_prompt = f"""
        Based on the following {{prompt}}, suggest instructions in order to guide the AI Model to:
        1. Show reasoning through using the chain-of-thought process
        2. Use inner-monologue only if it is recommended to hide parts of the thought process
        3. Self-review and check for missed information

        {{prompt}}: {expanded_prompt}
        
        Your output will be only the set of instructions in text format.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(reasoning_prompt)
    
    async def create_eval_criteria(self, expanded_prompt):
        """Generate evaluation criteria for the prompt output"""
        evaluation_prompt = f"""
        Create evaluation criteria for assessing the quality of the output for this {{prompt}}:
        1. List 1-3 specific criteria
        2. Briefly explain how to measure each criterion

        {{prompt}}: {expanded_prompt}
        
        Your output will be only the result of the information required above in text format.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(evaluation_prompt)
    
    async def suggest_references(self, expanded_prompt):
        """Suggest relevant references and explain how to use them"""
        reference_prompt = f"""
        For the following {{prompt}}, suggest relevant reference texts or sources that could help enhance the output of the prompt if possible, 
        and if not, do not return anything:
        1. List 0-3 potential references
        2. Briefly explain how to incorporate these references to enhance the prompt

        {{prompt}}: {expanded_prompt}
        
        Your output will be only the result of the information required above in a dictionary called "References" containing the references titles as keys, 
        and their corresponding explanation of incorporation as values. If no references will be suggested, return an empty dictionary.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(reference_prompt)

    async def suggest_tools(self, expanded_prompt, tools_dict):
        """Suggest relevant external tools or APIs"""
        tool_prompt = f"""
        For the following {{prompt}}, suggest relevant external tools from the provided {{tools_dict}} that can enhance the prompt for better execution. 
        If the prompt does not require tools for its output, it is highly-recommended to not return any tools:
        1. List 0-3 potential tools/APIs
        2. Briefly explain how to use these tools within the prompt

        {{prompt}}: {expanded_prompt}
        {{tools_dict}}: {tools_dict}
        
        Your output will be only the result of the information required above in a dictionary containing the suggested tools as keys, 
        and their corresponding way of usage with the prompt as values. If no tools will be suggested, return an empty dictionary.
        Do not return a general explanation of the generation process.
        """
        return await self.call_llm(tool_prompt)

    async def assemble_prompt(self, components):
        """Assemble all components into a cohesive advanced prompt"""
        assembly_prompt = f"""
        Assemble all the following {{components}} into a cohesive, and well-structured advanced prompt and do not generate a response for the prompt.
        Make sure to combine the {{reasoning_process}} and {{subtasks}} sections into one section called {{reasoning_process_and_subtasks}}.
        
        {{components}}: {components}

        Your output will be only the result of the tasks required above,
        which is an advanced coherent prompt generated from the combination of the given components dictionary. 
        Keep only the {{reasoning_process_and_subtasks}} section instead of the {{reasoning_process}} and {{subtasks}} sections in the output.
        Ensure that the assembled prompt maintains the delimiter structure of variables and the suggested persona.
        Make sure that each sub-section of the prompt is clear and has a title.
        The output is in plain text format and not a dictionary format.
        Do not return a general explanation of the generation process.
        Take the return-to-line symbol into consideration.
        Remove the "**Expanded Prompt**" header.
        """
        return await self.call_llm(assembly_prompt)
    
    async def auto_eval(self, assembled_prompt, evaluation_criteria):
        """Perform Auto-Evaluation and Auto-Adjustment"""
        auto_eval_prompt = f"""
        Perform any minor adjustments on the given {{prompt}} based on how likely its output will satisfy these {{evaluation_criteria}}.
        Only perform minor changes if it is necessary and return the updated prompt as output.
        If no changes are necessary, do not change the prompt and return it as output.
        
        {{prompt}}: {assembled_prompt}
        {{evaluation_criteria}}: {evaluation_criteria}
        
        Your output will be only the result of the tasks required above, which is an updated version of the {{prompt}}, in text format.
        Make sure to keep the {{evaluation_criteria}} in the output prompt.
        Do not return a general explanation of the generation process.
        Make sure there is no generated answer for the prompt. 
        Make sure to maintain the stucture of the {{prompt}}.
        """
        return await self.call_llm(auto_eval_prompt)

    async def enhance_prompt(self, basic_prompt, perform_eval=False):
        """Main method to enhance a basic prompt to an advanced one"""
        analysis = await self.analyze_input(basic_prompt)
        expanded_prompt = await self.expand_instructions(basic_prompt, analysis)
        
        evaluation_criteria, references, subtasks, reasoning, tools = await asyncio.gather(
            self.create_eval_criteria(expanded_prompt),
            self.suggest_references(expanded_prompt),
            self.decompose_task(expanded_prompt),
            self.add_reasoning(expanded_prompt),
            self.suggest_tools(expanded_prompt, tools_dict={}),
        )

        components = {
            "expanded_prompt": expanded_prompt,
            "references": references,
            "subtasks": subtasks,
            "tools": tools,
            "reasoning_process": reasoning,
            "evaluation_criteria": evaluation_criteria,
            
        }

        assembled_prompt = await self.assemble_prompt(components)
        
        if perform_eval:
            eveluated_prompt = await self.auto_eval(assembled_prompt, evaluation_criteria)
            advanced_prompt = eveluated_prompt
        else:
            advanced_prompt = assembled_prompt

        return {
            "advanced_prompt": advanced_prompt,
            "assembled_prompt": assembled_prompt,
            "components": components,
            "analysis": analysis,
        }

