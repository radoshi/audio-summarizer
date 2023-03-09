# Speech configuration
SPEECH_MODEL = "whisper-1"
RESPONSE_FORMAT = "verbose_json"  # For speech model

# Chat configuration
CHAT_MODEL = "gpt-3.5-turbo"


class MAX_TOKENS:
    SINGLE_SHOT = 500
    FIRST_CHUNK = 100
    NEXT_CHUNK = 100
    RESUMMARIZE = 250


TEMPERATURE = 0
MAX_WORDS = 1500  # Split inputs for more than than this.


class USER_PROMPT:
    ONE_SHOT = (
        "Summarize the following transcript of a podcast epised: \n\n{transcript}"
    )

    FIRST_CHUNK = "Summarize the transcript of a podcast in a succinct and truthful manner. \
        The podcast transcript has been broken up into {num_chunks} parts. \
        Do not mention the part number in your response. \
        Here is the first part: \n\n{chunk}"

    NEXT_CHUNK = 'Summarize the transcript of a podcast in a succinct and truthful manner. \
                The podcast transrcript has been broken up into {num_chunks} parts. \
                You are summarizing each part in isolation in order. \
                Do not say "In this part of the podcast" to reference the current part. \
                Here is the trancript {chunk_num}. \n\n \
                {chunk}'

    RESUMMARIZE = (
        "Summarize the following transcript of a podcast episode: \n\n{summary}"
    )


SYSTEM_PROMPT = "You are a helpful, effective, succinct, truthful assistant summarizing podcast transcripts."
