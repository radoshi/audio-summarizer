from constants import *

import click
import logging
import os
import openai
from pathlib import Path
import pydub


class Segment:
    def __init__(self, start, end, filename, dry_run=False):
        self.start = start
        self.end = end
        self.audio_filename = filename
        self.transcript = None
        self.transcript_filename = None
        self.dry_run = dry_run

    def __str__(self):
        return f"Segment(start={self.start}, end={self.end}, filename={self.audio_filename}, dry_run={self.dry_run})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            self.start == other.start
            and self.end == other.end
            and self.audio_filename == other.audio_filename
            and self.transcript == other.transcript
            and self.transcript_filename == other.transcript_filename
            and self.dry_run == other.dry_run
        )

    def transcribe(self) -> str:
        with open(self.audio_filename, "rb") as audio_file:
            logging.info("Transcribing audio file: %s", self.audio_filename)
            if not self.dry_run:
                transcript = openai.Audio.transcribe(
                    SPEECH_MODEL, audio_file, response_format=RESPONSE_FORMAT
                )
            else:
                transcript = {
                    "duration": 359.39,
                    "language": "english",
                    "task": "transcribe",
                    "text": "Testing transcript!",
                }
            logging.info("Completed transcribing audio file: %s", self.audio_filename)
            self.transcript = transcript
            return transcript

    def save_transcript(self, out):
        self.transcript_filename = out / f"{self.audio_filename.name}.json"
        self.transcript_filename.write_text(str(self.transcript))
        logging.info(f"Transcript saved to {self.transcript_filename}")


def create_segments(
    audio_filename: Path, out: Path, force=False, dry_run=False
) -> list:
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
            segment_filename = out / f"{audio_filename.name}.{i}.mp3"
            segment = Segment(i, i + 10 * 60 * 1000, segment_filename, dry_run=dry_run)
            segments.append(segment)
            if segment_filename.exists() and not force:
                logging.info("Segment %s already exists, skipping", segment_filename)
                continue
            audio_segment = audio[i : i + 10 * 60 * 1000]
            audio_segment.export(segment_filename, format="mp3")
            logging.info("Created segment %s", segment)
        return segments
    else:
        return [Segment(0, len(audio), audio_filename, dry_run=dry_run)]


def transcribe(audio_filename: Path, out: Path, force=False, dry_run=False) -> list:
    # audio_file cannot be null
    if not audio_filename:
        print("Error: audio_file is null")
        return None

    # if audio file is larger than 10 minutes, break it up into 10 minute chunks.
    segments = create_segments(audio_filename, out, force=force, dry_run=dry_run)

    # transcribe each segment
    for segment in segments:
        segment.transcribe()
        segment.save_transcript(out)

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
            ),
            max_tokens=tokens,
            temperature=TEMPERATURE,
        )
        summaries.append(response["choices"][0]["message"]["content"])

    # Resummarize the summaries.
    summary = " ".join(summaries)
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=create_messages(
            system=SYSTEM_PROMPT,
            user=USER_PROMPT.RESUMMARIZE.format(summary=summary),
        ),
        max_tokens=MAX_TOKENS.RESUMMARIZE,
        temperature=TEMPERATURE,
    )

    return response["choices"][0]["message"]["content"]


def summarize(transcript: str) -> str:
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
        return summarize_chunks(chunks)

    # Single chunk summary prompts are different from multi-chunk prompts
    user_prompt = USER_PROMPT.ONE_SHOT.format(transcript=transcript)
    logging.info("Requesting summary from OpenAI")
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=create_messages(SYSTEM_PROMPT, user_prompt),
        max_tokens=MAX_TOKENS.SINGLE_SHOT,
        temperature=TEMPERATURE,
    )
    return response["choices"][0]["message"]["content"]


def save_summary(summary, filename):
    with open(filename, "w") as f:
        f.write(str(summary["choices"][0]["message"]["content"]))
        logging.info("Summary saved to %s", filename)


@click.group
@click.option(
    "-log",
    "--loglevel",
    default="WARNING",
    help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "-key",
    "--apikey",
    default="",
    help="Set the OpenAI API key",
    envvar="OPENAI_API_KEY",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Don't actually run the commands"
)
@click.option(
    "--force", is_flag=True, default=False, help="Force overwrite of existing files"
)
@click.option(
    "-o",
    "--out",
    default="out",
    help="Set the output directory",
    type=click.Path(writable=True, file_okay=False),
)
@click.pass_context
def cli(ctx, loglevel, apikey, dry_run, force, out):
    ctx.ensure_object(dict)

    # Set the OpenAI API key
    if not apikey:
        print(
            "Error: API key not set. Set the OPENAI_API_KEY environment variable or use the --apikey argument."
        )
        exit(1)
    openai.api_key = apikey

    # Set the dry run flag
    ctx.obj["DRY_RUN"] = dry_run

    # Set the output directory
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ctx.obj["OUT_DIR"] = out

    # Set the force flag
    ctx.obj["FORCE"] = force

    # turn on logging
    logging.basicConfig(level=loglevel.upper())


@cli.command("transcribe")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def transcribe_command(ctx, filename):
    # Get the filename from the command line
    out = ctx.obj["OUT_DIR"]
    filename = Path(filename)
    transcript_file = out / f"{filename.name}.transcript.txt"

    force = ctx.obj["FORCE"]
    dry_run = ctx.obj["DRY_RUN"]

    # if the file already exists and --force is not set, exit
    if transcript_file.exists() and not force:
        print(
            f"Error: transcript {transcript_file} already exists. Use --force to overwrite."
        )
        exit(1)

    segments = transcribe(filename, out, force=force, dry_run=dry_run)

    # save the transcripts to corresponding files
    full_transcript = " ".join([segment.transcript["text"] for segment in segments])
    transcript_file.write_text(full_transcript)
    logging.info("Transcripts saved to %s", transcript_file)


@cli.command("summarize")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def summarize_command(ctx, filename):
    out = ctx.obj["OUT_DIR"]
    filename = Path(filename)
    transcript_file = out / f"{filename.name}.transcript.txt"
    summary_file = out / f"{filename.name}.summary.txt"

    # if the file already exists and --force is not set, exit
    force = ctx.obj["FORCE"]
    if summary_file.exists() and not force:
        print(
            f"Error: summary file {summary_file} already exists. Use --force to overwrite."
        )
        exit(1)

    # load the transcript from a file
    logging.info("Loading transcript from %s", transcript_file)
    if not transcript_file.exists():
        print(f"Error: transcript file {transcript_file} does not exist")
        exit(1)
    text = transcript_file.read_text()

    # summarize the transcript
    logging.info("Summarizing transcript")
    summary = summarize(text)

    logging.info("Saving final summary to %s", summary_file)
    summary_file.write_text(summary)

    print(f"Summary:\n{summary}")


@cli.command("segment")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def segment_command(ctx, filename):
    force = ctx.obj["FORCE"]
    dry_run = ctx.obj["DRY_RUN"]
    filename = Path(filename)
    segments = create_segments(filename, force, dry_run)
    logging.info(
        f'Created {len(segments)} segments: {", ".join([segment.audio_filename.name for segment in segments])}'
    )


if __name__ == "__main__":
    cli()
