# podcast-summarizer

## Summary
A toy summarizer for english language podcasts. Testing with audio lengths of 15-30 minutes. The summarizer uses OpenAI APIs to transcribe speech and generate summaries from the transcriptions.

## What's interesting
### Chunking and resummarization
Token lengths from long podcast transcripts exceed the `gpt-3.5-turbo` maximum of 4096 tokens. We overcome this by:
1. Chunk the transcript into batches. 
2. Summarize each chunk.
3. Resummarize the concatenation of all the chunks.

The batch size was adjusted by trial-and-error to 1000 tokens. The output of each batch must have sufficient size to accomodate the ideas. We used `MAX_TOKENS=100` corresponding to batch size of 1000. 

### Prompt tuning
The process of tuning prompts proved challenging. Key obstacles include:
1. Lack of repeatability due to GPT generating randomness. I made things more repeatable by setting `temperature=1`
2. Having a system to store the conversation to debug it later. Currently, this was overcome by a bunch of `logging.info` statements but is an avenue for future work.

## Usage
### Setup virtual env
```shell
python3 -m venv env
source env/bin/activate
```

### Transcribing audio
```shell
pip3 install -r requirements.txt
python summarize.py transcribe <audiofile>
```

### Summarizing transcripts
```shell
python summarize.py summarize <audiofile>
```

## Further work
### Debugging GPT interactions
The prompt tuning workflow essentially involves playing with some prompt language, re-running all prevous transcripts through the new prompts, and looking at the output. We could build a library to store a GPT session, that would allow easy pluggability into the playground for further tuning.

### Prompt tuning framework
Prompt tuning feels like a dark art. You're giving GPT a bunch of english and coaxing it to generate something interesting. Some of the prompts can create a lot of extra work or code - for example, trying to prime ChatGPT with some prompts followed by the actual prompt - this currently requires writing bespoke code, but presumably we could build a prompt tuning framework to make life easier.

## Acknowledgement
1. https://github.com/openai/openai-cookbook repo has some interesting ideas on prompt tuning.
2. https://platform.openai.com/playground?mode=chat OpenAI Playground is critical to do early prompt tuning.
