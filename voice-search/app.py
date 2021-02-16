__version__ = '0.0.1'

import os
import sys
import glob
import soundfile as sf
import torch
import shutil

from jina.flow import Flow
from jina import Document
from jina import MultimodalDocument



num_docs = int(os.environ.get('MAX_DOCS', 20))

def clean_workdir():
    if os.path.exists(os.environ['JINA_WORKSPACE']):
        shutil.rmtree(os.environ['JINA_WORKSPACE'])


def config():
    os.environ['JINA_PARALLEL'] = os.environ.get('JINA_PARALLEL', '1')
    os.environ['JINA_SHARDS'] = os.environ.get('JINA_SHARDS', '1')
    os.environ["JINA_WORKSPACE"] = os.environ.get("JINA_WORKSPACE", "workspace")

    os.environ['JINA_DATA_FILE'] = 'data/full.txt'
    os.environ['JINA_PORT'] = os.environ.get('JINA_PORT', str(65481))

    os.makedirs(os.environ['JINA_WORKSPACE'], exist_ok=True)


def index():
    
    data_path = os.path.join(os.path.dirname(__file__), os.environ.get('JINA_DATA_FILE', None))
    speech_paths = glob.glob("data/**/*.flac", recursive=True)
    if len(speech_paths) == 0:
        print("No audio files found, download the data first, using ./get_data.sh")
        exit(1)

    f = Flow.load_config('flows/index.yml')

    if os.path.isfile(data_path):
        print("file exists")
        docs = []
        with open(data_path, "r") as fi:
            lines = fi.readlines()
            for i, line in enumerate(lines[:num_docs]):
                #doc = Document(content=line,
                #    tags={'path': speech_paths[i]})
                text = Document(content=line, modality='text')
                audio = Document(content=speech_paths[i], modality='audio', mime_type="audio/flac")
                doc = MultimodalDocument(chunks=[text, audio])
                docs.append(doc)
        
        with f:
            print("data_path", data_path)
            #f.index_lines(filepath=data_path, batch_size=100, read_mode='r', size=num_docs)
            f.index(docs)
            
    else:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer

        tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
        model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
        docs = []
        for i, speech_path in enumerate(speech_paths[:num_docs]):
            # load audio
            audio_input, _ = sf.read(speech_path)
            
            # transcribe
            input_values = tokenizer(audio_input, return_tensors="pt").input_values
            logits = model(input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = tokenizer.batch_decode(predicted_ids)[0].lower()
            print("indexing file", i+1, "of", num_docs, speech_path.split("/").pop())
            print("transcription", transcription)
            
            with open(data_path, "a") as file:    
                file.write(transcription + "\n")

            #document = MultimodalDocument(modality_content_map={
            #    'text': transcription,
            #    'path': speech_path
            #})
            doc = Document(content=line,
                tags={'path': speech_paths[i]})
            docs.append(doc)
            

        with f:
            f.index_lines(lines=docs    , read_mode="r", size=len(ts))
        

def search():
    f = Flow.load_config('flows/query.yml')
    f.use_rest_gateway()
    with f:
        f.block()


# for test before put into docker
def dryrun():
    f = Flow.load_config('flows/query.yml')

    with f:
        pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('choose between "index/search/dryrun" mode')
        exit(1)
    if sys.argv[1] == 'index':
        config()
        clean_workdir()
        index()
    elif sys.argv[1] == 'search':
        config()
        search()
    elif sys.argv[1] == 'dryrun':
        config()
        dryrun()
    else:
        raise NotImplementedError(f'unsupported mode {sys.argv[1]}')
