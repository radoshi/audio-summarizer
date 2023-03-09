from constants import *

import argparse
import json
import logging
import os
import openai
from pathlib import Path
import pydub

DRY_RUN = False
OUT_DIR = Path("./out")


class Segment:
    def __init__(self, start, end, filename):
        self.start = start
        self.end = end
        self.audio_filename = filename
        self.transcript = None
        self.transcript_filename = None

    def __str__(self):
        return f"Segment(start={self.start}, end={self.end}, filename={self.audio_filename})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            self.start == other.start
            and self.end == other.end
            and self.audio_filename == other.audio_filename
        )

    def transcribe(self) -> str:
        with open(self.audio_filename, "rb") as audio_file:
            logging.info("Transcribing audio file: %s", self.audio_filename)
            if not DRY_RUN:
                transcript = openai.Audio.transcribe(
                    SPEECH_MODEL, audio_file, response_format=RESPONSE_FORMAT
                )
            else:
                transcript = {
                    "choices": [
                        {
                            "message": {
                                "content": "This is a test",
                            }
                        }
                    ],
                }
            logging.info("Completed transcribing audio file: %s", self.audio_filename)
            self.transcript = transcript
            return transcript

    def save_transcript(self):
        self.transcript_filename = OUT_DIR / f"{self.audio_filename.name}.json"
        self.transcript_filename.write_text(str(self.transcript))
        logging.info(f"Transcript saved to {self.transcript_filename}")


def create_segments(audio_filename: Path, force=False) -> list:
    if not audio_filename:
        raise ValueError("audio_filename cannot be null")

    # if audio file is larger than 10 minutes, break it up into 10 minute chunks
    logging.info("Checking audio length")
    audio = pydub.AudioSegment.from_file(audio_filename)
    logging.info("Audio length: %s", len(audio))

    if len(audio) > 10 * 60 * 1000:
        segments = []
        for i in range(0, len(audio), 10 * 60 * 1000):
            # if the file exists already and --force is not set, create the segment object but not the actual file
            segment_filename = OUT_DIR / f"{audio_filename.name}.{i}.mp3"
            segment = Segment(i, i + 10 * 60 * 1000, segment_filename)
            segments.append(segment)
            if segment_filename.exists() and not force:
                logging.info("Segment %s already exists, skipping", segment_filename)
                continue
            audio_segment = audio[i : i + 10 * 60 * 1000]
            audio_segment.export(segment_filename, format="mp3")
            logging.info("Created segment %s", segment)
        return segments
    else:
        return [Segment(0, len(audio), audio_filename)]


def transcribe(audio_filename: Path) -> list:
    # audio_file cannot be null
    if not audio_filename:
        print("Error: audio_file is null")
        return None

    # if audio file is larger than 10 minutes, break it up into 10 minute chunks.
    segments = create_segments(audio_filename)

    # transcribe each segment
    for segment in segments:
        segment.transcribe()
        segment.save_transcript()

    logging.info("Transcription complete")
    return segments


def create_messages(system, user, assistant=""):
    return [
        {
            "role": "system",
            "content": system,
        },
        {
            "role": "user",
            "content": user,
        },
    ]


def summarize_chunks(chunks):
    summaries = []
    for i, chunk in enumerate(chunks):
        logging.info("Summarizing chunk %s of %s", i + 1, len(chunks))
        user_prompt = assistant_prompt = ""
        if i == 0:
            user_prompt = USER_PROMPT.FIRST_CHUNK.format(
                chunk=chunk, num_chunks=len(chunks)
            )
            tokens = MAX_TOKENS.FIRST_CHUNK
        else:
            user_prompt = USER_PROMPT.NEXT_CHUNK.format(
                chunk=chunk, num_chunks=len(chunks), chunk_num=i + 1
            )
            tokens = MAX_TOKENS.NEXT_CHUNK

        response = openai.ChatCompletion.create(
            model=CHAT_MODEL,
            messages=create_messages(
                system=SYSTEM_PROMPT,
                user=user_prompt,
                assistant=assistant_prompt,
            ),
            max_tokens=tokens,
            temperature=TEMPERATURE,
        )
        summaries.append(response)
    return summaries


def summarize(transcript: str) -> list:
    """Summarize a transcript of a podcast episode. If the transcript is longer than 2000 words,
    split it into 2000 word chunks and summarize each chunk separately.

    Arguments:
        transcript {str} -- The transcript of a podcast episode.

    Returns:
        list -- A list of OpenAI ChatCompletion responses."""
    # if the length is greater than 2000, split it into 2000 word chunks
    words = transcript.split(" ")
    if len(words) > MAX_WORDS:
        logging.info("Transcript is too long, splitting into chunks")
        chunks = []
        for i in range(0, len(words), MAX_WORDS):
            chunk = " ".join(words[i : i + MAX_WORDS])
            chunks.append(chunk)
        logging.debug("Chunks: %s", chunks)
        summaries = summarize_chunks(chunks)
        return summaries

    # Single chunk summary prompts are different from multi-chunk prompts
    user_prompt = USER_PROMPT.ONE_SHOT.format(transcript=transcript)
    logging.info("Requesting summary from OpenAI")
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=create_messages(SYSTEM_PROMPT, user_prompt),
        max_tokens=MAX_TOKENS.SINGLE_SHOT,
        temperature=TEMPERATURE,
    )
    return [response]


def save_summary(summary, filename):
    with open(filename, "w") as f:
        f.write(str(summary["choices"][0]["message"]["content"]))
        logging.info("Summary saved to %s", filename)


if __name__ == "__main__":
    # Argparse
    parser = argparse.ArgumentParser(description="Summarize a podcast recording")
    parser.add_argument(
        "command", help="The command to run (segment, transcribe or summarize)"
    )
    parser.add_argument("filename", help="The filename of the audio file to summarize")
    parser.add_argument(
        "-log",
        "--loglevel",
        default="WARNING",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "-key",
        "--apikey",
        default="",
        help="Set the OpenAI API key",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually run the commands",
    )
    parser.add_argument(
        "-o",
        "--out",
        help="Set the output directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing files",
    )
    args = parser.parse_args()

    # Set the OpenAI API key
    key = args.apikey or os.environ.get("OPENAI_API_KEY")
    if not key:
        print(
            "Error: API key not set. Set the OPENAI_API_KEY environment variable or use the --apikey argument."
        )
        exit(1)
    openai.api_key = key

    # Set the dry run flag
    DRY_RUN = args.dry_run

    # Get the filename from the command line
    AUDIO_FILE = Path(args.filename)

    # Set the output directory
    if args.out:
        OUT_DIR = Path(args.out)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    TRANSCRIPT_FILE = OUT_DIR / f"{AUDIO_FILE.name}.transcript.txt"
    SUMMARY_FILE = OUT_DIR / f"{AUDIO_FILE.name}.summary.txt"

    # turn on logging
    logging.basicConfig(level=args.loglevel.upper())

    if args.command == "transcribe":
        # if the file already exists and --force is not set, exit
        if TRANSCRIPT_FILE.exists() and not args.force:
            print(
                f"Error: transcript {TRANSCRIPT_FILE} already exists. Use --force to overwrite."
            )
            exit(1)

        segments = transcribe(AUDIO_FILE)

        # save the transcripts to corresponding files
        full_transcript = " ".join([segment.transcript["text"] for segment in segments])
        TRANSCRIPT_FILE.write_text(full_transcript)
        logging.info("Transcripts saved to %s", TRANSCRIPT_FILE)

    elif args.command == "segment":
        segments = create_segments(AUDIO_FILE, args.force)
        logging.info(
            f'Created {len(segments)} segments: {", ".join([segment.audio_filename.name for segment in segments])}'
        )

    elif args.command == "summarize":
        # if the file already exists and --force is not set, exit
        if SUMMARY_FILE.exists() and not args.force:
            print(
                f"Error: summary file {SUMMARY_FILE} already exists. Use --force to overwrite."
            )
            exit(1)

        # load the transcript from a file
        logging.info("Loading transcript from %s", TRANSCRIPT_FILE)
        text = TRANSCRIPT_FILE.read_text()

        # summarize the transcript
        logging.info("Summarizing transcript")
        summaries = summarize(text)

        # save the summaries to files
        for i, summary in enumerate(summaries):
            filename = OUT_DIR / f"{AUDIO_FILE.name}.{i}.summary.json"
            logging.info("Saving chunk summary to %s", filename)
            filename.write_text(str(summary))

        # save the summary to a file
        logging.info("Saving final summary to %s", SUMMARY_FILE)
        overall_summary = " ".join(
            [summary.choices[0]["message"]["content"] for summary in summaries]
        )
        SUMMARY_FILE.write_text(overall_summary)

        print(f"Summary:\n{overall_summary}")

    else:
        print(f"Error: command {args.command} not recognized")
        exit(1)
