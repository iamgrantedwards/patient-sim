"""Local worker. Only explicit, validated dispatches can place a call."""
import asyncio
from dataclasses import asdict
import hashlib
import json
import re
import subprocess
import time

from google.protobuf.duration_pb2 import Duration
from livekit import api, rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, TurnHandlingOptions, cli, inference, room_io
from livekit.agents.beta.tools import EndCallTool

from .config import PROJECT_ROOT, load
from .lifecycle import disconnect_end, session_end, sip_failure
from .patient import DEFAULT_PATIENT, build_instructions
from .recording import preserve_recording
from .scenarios import get_scenario
from .transcript import CallArtifacts, finalize

AGENT_NAME = 'patient-sim'
server = AgentServer()
_calls: dict[str, CallArtifacts] = {}


async def save_call(ctx: JobContext) -> None:
    artifacts = _calls.pop(ctx.job.id, None)
    if artifacts is None:
        return
    try:
        report = ctx.make_session_report()
        artifacts.meta['recording_started_at'] = report.audio_recording_started_at
        # Keep only the explicit report fields needed; don't serialize provider objects/keys.
        artifacts.meta['sdk_version'] = report.sdk_version
        artifacts.meta['resolved_turn_settings'] = {
            'endpointing': dict(report.options.endpointing),
            'interruption': dict(report.options.interruption),
            'preemptive_generation': dict(report.options.preemptive_generation),
            'recording': dict(report.options.recording_options),
        }
        artifacts.meta['reported_model_usage'] = [entry.model_dump(mode='json') for entry in report.model_usage or []]
        artifacts.meta['recording'] = await asyncio.to_thread(
            preserve_recording, report.audio_recording_path, artifacts.directory,
        )
    except Exception as error:
        artifacts.meta['recording'] = {'status': 'error', 'error_type': type(error).__name__}
    finally:
        artifacts.end('worker_shutdown')
        artifacts.meta['status'] = 'ended'
        artifacts.save()
        artifacts.events.close()
        finalize(artifacts.directory, status='ended')
        # Close a connected SIP leg even if an error interrupted normal teardown.
        await ctx.delete_room()


@server.rtc_session(agent_name=AGENT_NAME, on_session_end=save_call)
async def entrypoint(ctx: JobContext) -> None:
    metadata = json.loads(ctx.job.metadata or '{}')
    call_id = metadata.get('call_id', '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}', call_id):
        raise ValueError('Explicit dispatch with a valid call_id is required')
    cfg = load()
    scenario = get_scenario(metadata.get('scenario', 'smoke'))
    instructions = build_instructions(DEFAULT_PATIENT, scenario, cfg.caller_id)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=PROJECT_ROOT, text=True))
    artifacts = CallArtifacts(PROJECT_ROOT / 'calls' / call_id, {
        'call_id': call_id, 'scenario_id': scenario.id, 'scenario_version': scenario.version,
        'scenario_requested': metadata.get('scenario', 'smoke'),
        'git_revision': revision, 'git_dirty': dirty, 'started_at': time.time(),
        'pipeline': cfg.pipeline, 'patient_record': asdict(DEFAULT_PATIENT),
        'prompt_sha256': hashlib.sha256(instructions.encode()).hexdigest(),
        'status': 'worker_started', 'ended_by': None,
        'sip': {'to': cfg.target_number, 'from': cfg.caller_id, 'status': 'not_started'},
        'answer_type': 'unknown', 'recording': {'status': 'pending'},
    })
    _calls[ctx.job.id] = artifacts
    timeout_task = None
    try:
        async def on_end_call(_event):
            artifacts.end('end_call_tool')

        end_tool = EndCallTool(
            end_instructions=None, delete_room=True,
            extra_description='As the patient, end after acknowledging the outcome and closing, including refusal or unavailability.',
            on_tool_called=on_end_call,
        )
        detector = (inference.TurnDetector(version='v1-mini')
                    if cfg.turn_detection == 'default' else cfg.turn_detection)
        session = AgentSession(
            stt=inference.STT(model=cfg.stt_model, language=cfg.stt_language),
            llm=inference.LLM(cfg.llm_model, extra_kwargs={'temperature': 0.4}),
            tts=inference.TTS(model=cfg.tts_model, voice=cfg.tts_voice, language='en'),
            turn_handling=TurnHandlingOptions(
                turn_detection=detector,
                endpointing={'mode': cfg.endpointing_mode, 'min_delay': cfg.endpointing_min_delay,
                             'max_delay': cfg.endpointing_max_delay},
                interruption={'mode': 'vad'},
                preemptive_generation={'enabled': False},
            ),
            ivr_detection=False, user_away_timeout=None,
        )

        @session.on('user_input_transcribed')
        def partial(event):
            artifacts.append('user_input_transcribed', event.model_dump(mode='json'))

        @session.on('conversation_item_added')
        def committed(event):
            artifacts.append('conversation_item_added', event.model_dump(mode='json'))
            if event.item.role in ('user', 'assistant'):
                artifacts.seen_turns.add(event.item.id)
            if len(artifacts.seen_turns) >= cfg.max_turns:
                artifacts.end('failsafe')
                artifacts.meta['failsafe_reason'] = 'max_turns'
                artifacts.save()
                session.shutdown(drain=False)

        @ctx.room.on('participant_disconnected')
        def disconnected(participant):
            if participant.identity != 'assessment-line':
                return
            reason = rtc.DisconnectReason.Name(participant.disconnect_reason)
            artifacts.append('sip_disconnected', {'reason': reason})
            artifacts.meta['sip']['disconnect_reason'] = reason
            answered = artifacts.meta['sip'].get('answered_at')
            if answered:
                artifacts.meta['sip']['duration_limit_may_have_fired'] = (
                    time.time() - answered >= cfg.max_call_seconds - 2
                )
            artifacts.end(disconnect_end(reason))
            artifacts.save()
            session.shutdown(drain=False)

        @session.on('close')
        def closed(event):
            if timeout_task is not None:
                timeout_task.cancel()
            artifacts.append('close', {'reason': event.reason.value})
            artifacts.end(session_end(event.reason.value, artifacts.meta.get('ended_by')))
            ctx.shutdown(reason=artifacts.meta['ended_by'])

        await asyncio.wait_for(ctx.connect(), timeout=30)
        # No on_enter greeting. Input/recording is prepared before the callee can speak.
        await asyncio.wait_for(session.start(
            Agent(instructions=instructions, tools=end_tool.tools), room=ctx.room,
            room_options=room_io.RoomOptions(
                participant_identity='assessment-line', text_input=False,
                audio_input=room_io.AudioInputOptions(noise_cancellation=None, auto_gain_control=False),
                delete_room_on_close=True,
            ),
            record={'audio': True, 'transcript': True, 'traces': True, 'redaction': False},
        ), timeout=45)
        artifacts.meta['sip']['status'] = 'dialing'
        artifacts.save()
        request = api.CreateSIPParticipantRequest(
            sip_trunk_id=cfg.sip_trunk_id, sip_call_to=cfg.target_number,
            sip_number=cfg.caller_id, room_name=ctx.room.name,
            participant_identity='assessment-line', participant_name='Assessment line',
            wait_until_answered=True, play_dialtone=False, krisp_enabled=False,
            ringing_timeout=Duration(seconds=cfg.ringing_timeout_seconds),
            max_call_duration=Duration(seconds=cfg.max_call_seconds),
        )
        try:
            info = await ctx.api.sip.create_sip_participant(request, timeout=cfg.ringing_timeout_seconds + 15)
        except api.SipCallError as error:
            artifacts.meta['sip'].update(status='failed', status_code=error.sip_status_code)
            artifacts.end(sip_failure(error.sip_status_code))
            ctx.shutdown(reason=artifacts.meta['ended_by'])
            return
        if artifacts.meta.get('ended_by'):
            return  # The callee may have hung up while the SIP request was completing.
        artifacts.meta['sip'].update(status='answered', answered_at=time.time(), call_id=info.sip_call_id)
        artifacts.meta['status'] = 'connected'
        artifacts.save()

        async def deadline():
            await asyncio.sleep(cfg.max_call_seconds)
            artifacts.meta['failsafe_reason'] = 'max_call_seconds'
            artifacts.end('failsafe')
            await ctx.delete_room()
            ctx.shutdown(reason='failsafe')

        timeout_task = asyncio.create_task(deadline())
        async def cancel_deadline():
            timeout_task.cancel()
        ctx.add_shutdown_callback(cancel_deadline)
        # The framework owns the session after entrypoint returns.
    except Exception as error:
        artifacts.meta['error_type'] = type(error).__name__
        artifacts.end('worker_error')
        await ctx.delete_room()
        ctx.shutdown(reason='worker_error')


if __name__ == '__main__':
    cli.run_app(server)
