FROM jinaai/jina:1.0

COPY . /workspace
WORKDIR /workspace

RUN apt-get update && pip install -r requirements.txt

RUN python app.py dryrun

ENTRYPOINT ["python", "app.py"]
