from google import genai
import os


data_folder='data'

entries = os.listdir(data_folder)

#client = genai.Client(api_key="AIzaSyA06kaBdq6WSObuQ9UnjhfhcHFW4BWpWOQ")

#response = client.models.generate_content(
#    model="gemini-2.0-flash",
#    contents=["How does AI work in a few lines?"]
#)
#print(response.text)
