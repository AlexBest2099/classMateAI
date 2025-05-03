import google.generativeai as genai
import os
import json
from create_database import *


from add_to_database import process_pdf_to_db


def process_and_add_file():

    initialize_database_schema('database.db')

    database='database.db'
    GEMINI_PROMPT = """
    Please analyze the provided content according to the database schema and processing logic defined by the associated Python script. Generate ONLY a JSON object containing "content", "mistakes", and "good_answers" keys.
    Instructions:

    Content Extraction ("content" key):Identify the hierarchy: Subject(s) -> Topic(s) -> Subtopic(s).
    For each Topic and Subtopic, extract source location details (page_number, location_description/location_detail, keywords as applicable). Use null for any unidentifiable location details.
    Populate the "content" list following the nested structure expected by the script.
    Mistake Identification ("mistakes" key):Only extract mistakes if the source document type is homework, exam, graded work, or if mistakes are explicitly marked in the text. Otherwise, this should be an empty list ([]).
    For each mistake, record: location (page_number, location_detail - use null if unknown), description, type, details, relevant_topic name, and relevant_subtopic name (if applicable).
    Use the source filename and filepath provided externally (which will be added later) for the source_filename and source_filepath fields within each mistake object.
    If relevant_topic or relevant_subtopic cannot be confidently identified, use null or omit the entry based on the script's handling logic (assume linking to the topic is mandatory if a mistake is recorded). Do not invent links.
    Good Answer Identification ("good_answers" key):Only extract good answers if the source document type is homework, exam, solution set, or if good examples are explicitly marked. Otherwise, this should be an empty list ([]).
    For each good answer, record: location (page_number, location_detail - use null if unknown), description, relevant_topic name, and relevant_subtopic name (if applicable).
    Use the source filename and filepath provided externally (which will be added later) for the source_filename and source_filepath fields within each good answer object.
    Handle missing topic/subtopic links as described for mistakes. The sources should only contain the filename and the filepath the filepath,  only one entry. The descriptions you should add youself, based on the content. 
    Same with keywords for localizaiton try and find them, and specify. If there is page number on the document dont use it, use only the actual page counter. Make as many topics as possible, you can ignore subtopics and replace them with null
    General Rules:Do not invent data. Use null for optional fields where information cannot be extracted. Make sure the topics extracted are correct, Make sure none you dont create NoneType object
    Adhere strictly to the JSON structure expected by the data insertion logic in the associated Python script. Only output the raw JSON object, nothing else before or after it.
    """
    entries=os.listdir('data')
    for filename in entries:

        if not check_file_exists_in_db(database,filename):
            name1, extension = os.path.splitext(filename)
            if extension=='.txt':
                GEMINI_PROMPT=GEMINI_PROMPT+f'\n Since this document is a text file instead of page number give row number but keep the same name in the json'
            file='data/'+filename
            file_name_to_gemini=f'\n The name of the information file is'+filename+f'\n And the filepath is '+file
            topics=get_topic_id_pairs_as_string()
            GEMINI_PROMPT=GEMINI_PROMPT+file_name_to_gemini
            GEMINI_PROMPT=GEMINI_PROMPT+f'\n This is the current topic list, make it so that every new topic if its name would be similar or mean the same thing to have use the topic name and id already there, the format is topic name: topic id, here is the topic list:\n'+topics
            process_pdf_to_db(file,database,GEMINI_PROMPT)
        else:
            print(f'File {filename} is already in the database')