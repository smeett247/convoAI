from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os
import platform

load_dotenv()

client = OpenAI()
assistants_id_list = [-1]
vs_id_list = [-1]


def write_to_file():
    print("Generating .txt files...")
    assistant_data = client.beta.assistants.list().data
    
    assistants_id_list.clear()
    assistants_id_list.append(-1)
    
    vs_id_list.clear()
    vs_id_list.append(-1)
    
    with open("openai-debug-assistant.txt","w") as file:
        file.write("==================Assistant Data=================\n\n")
        for assistant in assistant_data:
            sno = len(assistants_id_list)
            assistants_id_list.append(assistant.id)
            
            file.write(f"S.No : {sno}\n")
            file.write(f"Assistant ID : {assistant.id}\n")
            file.write(f"Created At: {datetime.fromtimestamp(assistant.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Name : {assistant.name}\n")
            file.write(f"Instructions : {assistant.instructions}\n")
            file.write(f"Model : {assistant.model}\n")
            file.write(f"Tools: {str(assistant.tools)}\n")
            file.write("\n\n-------------\n\n")
            
    vector_store_data = client.beta.vector_stores.list().data
    with open("openai-debug-vs.txt","w") as file:
        file.write("==================Vector Store Data=================\n\n")
        for vs in vector_store_data:
            sno = len(vs_id_list)
            vs_id_list.append(vs.id)
            file.write(f"S.No : {sno}\n")
            file.write(f"Vector Store ID : {vs.id}\n")
            file.write(f"Created At: {datetime.fromtimestamp(vs.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Name : {vs.name}\n")
            file.write(f"File Counts : {vs.file_counts}\n")
            file.write(f"Status : {vs.status}\n")
            file.write(f"Usage in Bytes: {vs.usage_bytes}\n")
            file.write(f"Last Active At: {datetime.fromtimestamp(vs.last_active_at).strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write("\n\n-------------\n\n")
            

assistant_id_to_delete = []
vector_store_to_delete = []

while True:
    write_to_file()
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    print(f"Using API Key ending with: {os.environ["OPENAI_API_KEY"][-5:]}")
    print("""
        Open AI Deletion Tool by NotTheRightGuy
Check .txt generated in root directory for your VS and Assistant Information
        
    1. Delete Assistants
    2. Delete Vector Stores
    3. Exit
        """)

    prompt = int(input(">>> "))
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    if prompt == 1:
        print("Look at the .txt file generated to find serial number")
        ids = list(map(int,input("Enter Serial number of Assistant ID seperated by space:\n>>> ").split(" ")))
        
        for as_id in ids:
            assistant_id_to_delete.append(assistants_id_list[as_id])
            print("Deleting Assistant with ID: " + assistants_id_list[as_id])
            client.beta.assistants.delete(assistants_id_list[as_id])
        assistant_id_to_delete.clear()
        print("Assistants Deleted!")
        print("Generating .txt files again...")
        continue
    
    elif prompt == 2:
        print("Look at the .txt file generated to find serial number")
        ids = list(map(int,input("Enter Serial number of Vector store ID seperated by space:\n>>> ").split(" ")))
        for vs_id in ids:
            vector_store_to_delete.append(vs_id_list[vs_id])
            print("Deleting Vector Store with ID: " + vs_id_list[vs_id])
            client.beta.vector_stores.delete(vs_id_list[vs_id])
        vector_store_to_delete.clear()
        print("Vector Store Deleted!")
        continue
    
    elif prompt == 3:
        print("Exiting...")
        break

    else:
        print("Invalid Input!")
        continue
    
    