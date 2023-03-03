import argparse
import os
import openai
import logging
import json

from pathlib import Path

DRY_RUN = False
OUT_DIR = Path("./out")
SPEECH_MODEL = "whisper-1"
RESPONSE_FORMAT = "verbose_json"
CHAT_MODEL = "gpt-3.5-turbo"
SYSTEM_PROMPT = "You are a helpful, effective, succinct, truthful assistant summarizing podcast transcripts."
USER_PROMPT = "Summarize the following podcast transcript into bullet points: "
MAX_TOKENS = 200
TEMPERATURE = 0.2


def transcribe(audio_filename: Path) -> str:
    # audio_file cannot be null
    if not audio_filename:
        print("Error: audio_file is null")
        return None

    with open(audio_filename, "rb") as audio_file:
        logging.debug("Transcribing audio file: %s", audio_filename)
        if not DRY_RUN:
            transcript = openai.Audio.transcribe(
                SPEECH_MODEL, audio_file, response_format=RESPONSE_FORMAT
            )
        else:
            transcript = {
                "transcript": "This is a test transcript. It is only a test.",
                "confidence": 0.999,
            }
        logging.debug("Transcribing complete.")
        return transcript


def create_messages(system_content, user_content):
    return [
        {
            "role": "system",
            "content": system_content,
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def summarize(transcript):
    user_prompt = f"{USER_PROMPT} {transcript}"
    logging.debug("Requesting summary from OpenAI")
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=create_messages(SYSTEM_PROMPT, user_prompt),
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
    return response


def save_summary(summary, filename):
    with open(filename, "w") as f:
        f.write(str(summary["choices"][0]["message"]["content"]))
        logging.info("Summary saved to %s", filename)


if __name__ == "__main__":
    # Argparse
    parser = argparse.ArgumentParser(description="Summarize a podcast recording")
    parser.add_argument("filename", help="The filename of the audio file to summarize")
    parser.add_argument("command", help="The command to run (transcribe or summarize)")
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

    TRANSCRIPT_FILE = OUT_DIR / f"{AUDIO_FILE.name}.transcript.json"
    SUMMARY_FILE = OUT_DIR / f"{AUDIO_FILE.name}.summary.json"

    # turn on logging
    logging.basicConfig(level=args.loglevel.upper())

    if args.command == "transcribe":
        # if the file already exists and --force is not set, exit
        if TRANSCRIPT_FILE.exists() and not args.force:
            print(
                f"Error: transcript file {TRANSCRIPT_FILE} already exists. Use --force to overwrite."
            )
            exit(1)

        transcript = transcribe(AUDIO_FILE)

        # save the transcript to a file
        logging.info("Saving transcript to %s", TRANSCRIPT_FILE)
        TRANSCRIPT_FILE.write_text(str(transcript))

    elif args.command == "summarize":
        # if the file already exists and --force is not set, exit
        if SUMMARY_FILE.exists() and not args.force:
            print(
                f"Error: summary file {SUMMARY_FILE} already exists. Use --force to overwrite."
            )
            exit(1)

        # load the transcript from a file
        logging.info("Loading transcript from %s", TRANSCRIPT_FILE)
        transcript = TRANSCRIPT_FILE.read_text()

        # read the transcript as json
        logging.info("Reading transcript as JSON")
        transcript = json.loads(transcript)
        text = transcript["text"]

        # summarize the transcript
        logging.info("Summarizing transcript")
        summary = summarize(text)

        # save the summary to a file
        logging.info("Saving summary to %s", SUMMARY_FILE)
        SUMMARY_FILE.write_text(str(summary))

        print(summary["choices"][0]["message"]["content"])

    else:
        print("Error: command not recognized")
        exit(1)
