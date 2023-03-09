# podcast-summarizer

<img alt="DALL-E: 3d render of a stylish podcast microphone on a light yellow background" src="https://rushabhdoshi.com/assets/microphone.png" width="300px"/>

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

## Examples

### [No Stupid Questions Birthday Episode](https://freakonomics.com/podcast/what-should-you-do-on-your-birthday/)

GPT Summary

> In this podcast episode, Angela Duckworth and Stephen Dubner discuss the history and commercialization of birthdays, as well as alternative ways to celebrate loved ones. They also explore the concept of temporal landmarks and their role in reflecting on one's life and making changes. The hosts share personal experiences with birthday rituals and surprise parties, and acknowledge the value of social rituals in human societies. They also question the tradition of blowing out candles on a cake and suggest the need for a "spit guard." The episode concludes with a fact check and promotion of their other shows, along with information on how to listen ad-free and submit questions for future episodes.

Author Summary

> Birthdays! Why do Americans prefer Thanksgiving and the Fourth of July to theirs? Why do they make Stephen think of molasses and chicken feed? And is “Happy Birthday” the worst song ever written?

### [Techmeme Ride Home Thursday 3/02](https://www.ridehome.info/show/techmeme-ride-home/thu-0302-and-right-on-schedule-here-come-the-apis/)

GPT Summary

> OpenAI has launched a chat GPT API for businesses, with Snap and Shopify among the early adopters. Microsoft has updated its Bing chatbot to let users toggle between creative, balanced, and precise tones. Microsoft researchers have unveiled Cosmos One, a multimodal LLM they claim can understand image content and pass visual IQ tests. Apple blocked an update to the BlueMail app that added ChachiBT-powered features over inappropriate content concerns requiring a 17-plus age limit. Snap plans to let users pause streaks by buying streak restores for 99 cents each time and will soon let Snapchat Plus subscribers pause streaks indefinitely. The podcast also features an ad for NFT Talon and Radial Development Group. The segment ends with a discussion on in-app purchases and how TikTok has generated more revenue than Facebook, Instagram, Snapchat. Neuralink, a company founded in 2016, is set to begin human trials for a brain implant to treat conditions such as paralysis and blindness. However, the US FDA rejected the company's application due to safety concerns regarding the device's lithium battery, the potential migration of the implant's wires, and the device's removal without damaging brain tissue.

Author Summary

> A ChatGPT API for business is here. Microsoft gives Bing those nobs and dials that I’ve been talking about. What are multimodal LLMs? New turmoil in crypto, this time around one of the big crypto friendly banks. How is it going in terms of social platforms diversifying into subscription revenue? And why the FDA has rejected Neuralink’s applications to begin human testing of brain implants.

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
