# Speech configuration
SPEECH_MODEL = "whisper-1"
RESPONSE_FORMAT = "verbose_json"  # For speech model

# Chat configuration
CHAT_MODEL = "gpt-3.5-turbo"


class MAX_TOKENS:
    SINGLE_SHOT = 500
    FIRST_CHUNK = 100
    NEXT_CHUNK = 100
    RESUMMARIZE = 200


TEMPERATURE = 0
MAX_WORDS = 1500  # Split inputs for more than than this.


class USER_PROMPT:
    ONE_SHOT = (
        "Summarize the following podcast transcript into bullet points. {transcript}"
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


SYSTEM_PROMPT = "You are a helpful, effective, succinct, truthful assistant summarizing podcast transcripts."

# class USER_PROMPT:
#     ONE_SHOT = (
#         "Summarize the following podcast transcript into bullet points. {transcript}"
#     )

#     FIRST_CHUNK = "Summarize the transcript of a podcast in a succinct and truthful manner. \
#         The podcast transcript has been broken up into {num_chunks} parts. \
#         Here is part one: \n\n{chunk}"

#     NEXT_CHUNK = "Summarize the transcript of a podcast in a succinct and truthful manner. \
#                 The podcast transrcript has been broken up into {num_chunks} parts. \
#                 You are summarizing each part in isolation in order. \
#                 Here is the transcript for part {chunk_num}. \n\n \
#                 {chunk}"
# The podcast hosts discuss the history and purpose of birthday celebrations, including the repetition of the "Happy Birthday" song and the role of commerce in promoting the celebration. They also explore the idea of using temporal landmarks to mark time and reflect on life. The hosts share their personal views on celebrating birthdays and suggest alternative ways to celebrate loved ones. The podcast ends with a discussion on how birthdays rank among other holidays in America. In part 2 of the podcast, the hosts discuss the idea of reflecting on one's birthday and the rituals associated with it. They mention that some people write in their journals on their birthdays to reflect on their lives. The hosts also talk about the significance of temporal landmarks like birthdays and how they can make people pay attention to the meaning in their lives. They mention a study that shows people are more likely to participate in a marathon or have an affair before reaching a birthday that ends in zero. In part 3 of the podcast, Angela and Stephen discuss the importance of shared rituals and temporal landmarks like birthdays. They also talk about the history of the Happy Birthday song and the controversy surrounding its copyright. Stephen expresses his dislike for blowing out candles on a cake and suggests the need for a "spit guard" invention. They end the episode by asking listeners to share their favorite birthday traditions. The final part of the podcast discusses the upcoming episode on slothful behavior and how it can actually be a virtue if it conserves energy for things that matter. The podcast is part of the Freakonomics Radio Network, which includes other shows like Freakonomics Radio and People I Mostly Admire. The episode was mixed by Eleanor Osborne and produced by Stitcher and Renbud Radio. The show's theme song is "And She Was" by Talking Heads. Listeners can follow the
