"""Durable raw events and a conservative, recoverable conversation transcript."""
import argparse
import json
import os
from pathlib import Path
import time


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def read_events(path: Path) -> list[dict]:
    events = []
    lines = path.read_text(errors='replace').splitlines()
    for index, line in enumerate(lines):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # A killed process may leave its last append incomplete. Keep earlier lines.
            if index != len(lines) - 1:
                raise ValueError(f'Corrupt event at line {index + 1}') from None
    return events


def reconcile(events: list[dict]) -> tuple[list[dict], list[dict]]:
    turns, seen, pending = [], set(), []
    for event in events:
        if event['type'] == 'user_input_transcribed':
            pending.append(event['data'])
        if event['type'] != 'conversation_item_added':
            continue
        item = event['data']['item']
        if item.get('type') != 'message' or item.get('role') not in ('user', 'assistant'):
            continue
        if item['id'] in seen:
            continue
        seen.add(item['id'])
        if item['role'] == 'user':
            # STT item IDs are provider-specific, not necessarily chat message IDs.
            # Keep all raw events; consume the pending STT batch on the remote commit.
            pending.clear()
        turns.append({
            'idx': len(turns), 'item_id': item['id'],
            'role': 'remote' if item['role'] == 'user' else 'patient',
            'text': '\n'.join(x for x in item.get('content', []) if isinstance(x, str)),
            'status': 'partial' if item.get('interrupted') else 'completed',
            'interrupted': item.get('interrupted', False),
            'event_received_at': event['received_at'],
            'audio_start_ms': None, 'audio_end_ms': None,
            'our_response_ms': None, 'their_response_ms': None, 'overlap_ms': None,
        })
    # Unmatched STT is explicitly separate, never promoted into a second conversation turn.
    return turns, pending


def finalize(directory: Path, status: str = 'recovered_partial') -> dict:
    meta = json.loads((directory / 'meta.json').read_text())
    turns, pending = reconcile(read_events(directory / 'events.jsonl'))
    result = {
        'call_id': meta['call_id'], 'scenario_id': meta['scenario_id'],
        'status': status, 'ended_by': meta.get('ended_by'),
        'turns': turns, 'uncommitted_transcriptions': pending,
        'claimed_state': None, 'consistency': None, 'verified_state': None,
        'timing_status': 'not_measured; event times are not audio offsets',
    }
    write_json(directory / 'transcript.json', result)
    lines = [f"Call {meta['call_id']} — {status}", "Audio timings not yet measured.", ""]
    lines += [f"{t['idx']:03d} {t['role']} [{t['status']}]: {t['text']}" for t in turns]
    if pending:
        lines += ['', 'Uncommitted STT events retained in transcript.json; not additional turns.']
    (directory / 'transcript.txt').write_text('\n'.join(lines) + '\n')
    return result


class CallArtifacts:
    def __init__(self, directory: Path, meta: dict):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.meta = meta
        self.events = (directory / 'events.jsonl').open('x', buffering=1)
        self.seen_turns: set[str] = set()
        self.save()

    def save(self) -> None:
        write_json(self.directory / 'meta.json', self.meta)

    def append(self, event_type: str, data: dict) -> None:
        self.events.write(json.dumps({
            'type': event_type, 'received_at': time.time(), 'data': data,
        }, ensure_ascii=False) + '\n')
        self.events.flush()
        os.fsync(self.events.fileno())

    def end(self, reason: str) -> None:
        # A later generic session-close event must not overwrite the specific cause.
        if not self.meta.get('ended_by'):
            self.meta.update(ended_by=reason, ended_at=time.time())
            self.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recover transcripts from persisted raw events')
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = finalize(args.directory)
    print(f"Recovered {len(result['turns'])} committed turns; audio not certified.")
