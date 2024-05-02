from io import BytesIO
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse ,FileResponse,  JSONResponse, HTMLResponse
from tempfile import NamedTemporaryFile
from gtts import gTTS
import os, io
from io import BytesIO
import requests
from openai import AzureOpenAI
from PIL import Image
import langdetect
import shutil

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Language Learn API"}

@app.get("/chat/{text}")
def text_to_text(text : str):
    response = chat(text)
    return response

@app.get("/tts/{text}")
def text_to_speech(text : str):
    response = chat(text)
    lang=langdetect.detect(response)
    mp3 = io.BytesIO()
    gTTS(text=response, lang=lang).write_to_fp(mp3)
    mp3.seek(0)
    return StreamingResponse(mp3, media_type="audio/mp3")

@app.get("/dalle/{text}")
def text_to_image(text : str):
    image_url = get_image_dalle(text)
    try:

        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")

        content_type = response.headers.get("Content-Type", "image/jpeg")
        image_stream = BytesIO(response.content)

        return StreamingResponse(content=image_stream, media_type=content_type)
    
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Failed to fetch image")
    

@app.post("/voice_to_voice_chat/")
def upload_audio(file: UploadFile = File(...)):
    print(os.getcwd())
    #print(os.listdir())
    path = "audio.mp3"
    out_path = "out.mp3"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print("save sucessfully")
    response = str(speech_recog(path))
    response = chat(response)
    print("Out: ", response)
    os.remove(path)  # Supprimer le fichier audio temporaire
    
    lang=langdetect.detect(response)
    tts = gTTS(text=response, lang = lang)
    tts.save(out_path)
    return FileResponse(out_path, media_type="audio/mp3",  filename="speech.mp3")
    

@app.post("/image_to_voice/")
async def image_to_text(file: UploadFile = File(...)):
    # Enregistrer le fichier audio téléchargé temporairement
    with NamedTemporaryFile(delete=False) as tmp_audio:
        tmp_audio.write(await file.read())
        tmp_audio_path = tmp_audio.name

    response = "Gpt4 Not available yes"
    lang="en"
    mp3 = io.BytesIO()
    gTTS(text=response, lang=lang).write_to_fp(mp3)
    mp3.seek(0)
    return StreamingResponse(mp3, media_type="audio/mp3")
   

def get_image_dalle(user_prompt,
                               image_dimension="1024x1024",
                               image_quality="hd",
                               model="Dalle3",
                               nb_final_image=1):
   
   open_client = AzureOpenAI(
    api_key="cc5db52f27ee49c489f80a503d7604eb",  
    api_version="2023-12-01-preview",
    azure_endpoint="https://vision-plus-openai.openai.azure.com/"
   )
   response = open_client.images.generate(
     model = model,
     prompt = user_prompt,
     #size = image_dimension,
     #quality = image_quality,
     n=nb_final_image,
   )


   image_url = response.data[0].url
   return image_url
    
def chat(text):
    open_client = AzureOpenAI(
    api_key="1b111ce8aadb4eb19620f64e2fa1b7fd",  
    api_version="2023-12-01-preview",
    azure_endpoint="https://gptlearn.openai.azure.com/"
    )
    chat_completion = open_client.chat.completions.create(
        model="subtitlecorrect", # model = "deployment_name".
        messages=[
            {"role": "system", "content": "You are my virtual english friend."},
            {"role": "user", "content": f"{text}"},
           
            ]
  
    ) 
    reponse = chat_completion.choices[0].message.content
    return  reponse


def speech_recog(audio_path):
    open_client = AzureOpenAI(
        api_key="0e457189a9644f148f4c4038ddb669af", 
            api_version="2024-02-01",
            azure_endpoint = "https://jacques.openai.azure.com/"
        )
    deployment_id = "whisperlearn" #This will correspond to the custom name you chose for your deployment when you deployed a model."
    



    result = open_client.audio.transcriptions.create(
        file=open(audio_path, "rb"),            
        model=deployment_id
    )

    text =  result.text
    return text

def image_to_text():
    api_base = "https://gpt4learn.openai.azure.com/"
    api_key= "65d90cef613149ef9cc61ea1373bbaec"
    deployment_name = 'gpt_image_meaning'
    api_version = '2023-12-01-preview' # this might change in the future

    client = AzureOpenAI(
        api_key=api_key,  
        api_version=api_version,
        base_url=f"{api_base}/openai/deployments/{deployment_name}"
    )

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            { "role": "system", "content": "You are a helpful assistant." },
            { "role": "user", "content": [  
                { 
                    "type": "text", 
                    "text": "Describe this picture:" 
                },
                { 
                    "type": "image_url",
                    "image_url": {
                        "url": "https://raw.githubusercontent.com/kokou-sekpona/langapp/main/avatar/horses-2904536_640.jpg?token=GHSAT0AAAAAACQLP63LFBXIQZPR2TLJXHX2ZRO5RGA"
                    }
                }
            ] } 
        ],
        max_tokens=2000 
    )

    print(response)