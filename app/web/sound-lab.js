/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const status = $('sound-status');
  const playSketch = $('play-sketch');
  const stopSound = $('stop-sound');
  const volume = $('master-volume');
  const keeperVideo = $('keeper-video');
  const presetButtons = Array.from(document.querySelectorAll('[data-audition]'));
  const cueRows = Array.from(document.querySelectorAll('[data-cue-row]'));

  const cues = Object.freeze([
    Object.freeze({ id: 'pulse', at: 0, duration: 12.8 }),
    Object.freeze({ id: 'tick', at: 2, duration: .75 }),
    Object.freeze({ id: 'reveal', at: 5, duration: 1.8 }),
    Object.freeze({ id: 'bed-open', at: 8, duration: 1.4 }),
    Object.freeze({ id: 'bed-hold', at: 9.6, duration: 1.4 }),
    Object.freeze({ id: 'bed-resolve', at: 11.2, duration: 1.6 }),
  ]);

  let built = false;
  let starting = false;
  let playing = false;
  let scheduledIds = [];
  let pulse;
  let tick;
  let reveal;
  let bed;
  let air;
  let master;

  function setStatus(message, state = 'ready') {
    status.textContent = message;
    status.dataset.state = state;
  }

  function setActive(id = '') {
    cueRows.forEach((row) => row.toggleAttribute('data-active', row.dataset.cueRow === id));
  }

  function setPlaying(value) {
    playing = value;
    playSketch.disabled = value || starting;
    stopSound.disabled = !value;
    presetButtons.forEach((button) => { button.disabled = starting; });
  }

  function clearTransport() {
    const transport = Tone.getTransport();
    scheduledIds.forEach((id) => transport.clear(id));
    scheduledIds = [];
    transport.stop();
    transport.position = 0;
    setActive('');
  }

  function buildGraph() {
    const limiter = new Tone.Limiter(-1).toDestination();
    master = new Tone.Volume(Number(volume.value)).connect(limiter);
    const cueBus = new Tone.Gain(.8).connect(master);

    pulse = new Tone.MembraneSynth({
      pitchDecay: .028,
      octaves: 4,
      oscillator: { type: 'sine' },
      envelope: { attack: .001, decay: .22, sustain: 0, release: .08 },
    }).connect(cueBus);

    const tickFilter = new Tone.Filter({ type: 'bandpass', frequency: 2600, Q: 2.4 }).connect(cueBus);
    tick = new Tone.NoiseSynth({
      noise: { type: 'pink' },
      envelope: { attack: .001, decay: .028, sustain: 0, release: .01 },
    }).connect(tickFilter);

    const revealSpace = new Tone.FeedbackDelay({ delayTime: .135, feedback: .18, wet: .17 }).connect(cueBus);
    reveal = new Tone.PolySynth(Tone.FMSynth, {
      harmonicity: 1.5,
      modulationIndex: 2.1,
      envelope: { attack: .005, decay: .4, sustain: .12, release: .7 },
      modulationEnvelope: { attack: .006, decay: .16, sustain: 0, release: .24 },
    }).connect(revealSpace);

    bed = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: 'triangle' },
      envelope: { attack: .055, decay: .5, sustain: .34, release: 1.25 },
    }).connect(cueBus);

    const airFilter = new Tone.Filter({ type: 'highpass', frequency: 1800 }).connect(cueBus);
    air = new Tone.NoiseSynth({
      noise: { type: 'white' },
      envelope: { attack: .22, decay: .32, sustain: 0, release: .22 },
    }).connect(airFilter);
  }

  async function ensureAudio() {
    if (built) return;
    if (!window.Tone) throw new Error('The local Tone.js asset did not load.');
    if (starting) return;
    starting = true;
    setPlaying(false);
    setStatus('Starting browser audio…', 'starting');
    await Tone.start();
    buildGraph();
    Tone.getTransport().bpm.value = 96;
    built = true;
    starting = false;
    setPlaying(false);
    setStatus('Audio ready · local Tone.js 15.1.22', 'ready');
  }

  function trigger(id, time) {
    if (id === 'pulse') {
      pulse.triggerAttackRelease('A1', '8n', time, .78);
      pulse.triggerAttackRelease('A1', '8n', time + .75, .55);
    }
    if (id === 'tick') {
      [0, .25, .5].forEach((offset, index) => {
        tick.triggerAttackRelease('32n', time + offset, .18 + index * .05);
      });
    }
    if (id === 'reveal') {
      air.triggerAttackRelease('8n', time, .24);
      reveal.triggerAttackRelease(['D3', 'A3', 'D4'], '2n', time + .05, .42);
    }
    if (id === 'bed-open') bed.triggerAttackRelease(['G2', 'D3', 'B3'], '2n', time, .25);
    if (id === 'bed-hold') bed.triggerAttackRelease(['A2', 'E3', 'C4'], '2n', time, .21);
    if (id === 'bed-resolve') {
      bed.triggerAttackRelease(['G2', 'D3', 'G3'], '2n', time, .24);
      pulse.triggerAttackRelease('G1', '4n', time + .35, .3);
    }
  }

  async function playCueSketch() {
    try {
      await ensureAudio();
      keeperVideo.pause();
      clearTransport();
      const transport = Tone.getTransport();
      scheduledIds = cues.map((cue) => transport.scheduleOnce((time) => {
        trigger(cue.id, time);
        Tone.getDraw().schedule(() => setActive(cue.id), time);
      }, cue.at));
      setPlaying(true);
      setStatus('Playing 12.8s sound sketch · 96 BPM', 'playing');
      transport.start();
      Tone.getDraw().schedule(() => {
        setPlaying(false);
        setActive('');
        setStatus('Sketch finished · local Tone.js 15.1.22', 'ready');
      }, 12.8);
    } catch (error) {
      starting = false;
      setPlaying(false);
      setStatus(`Audio unavailable: ${error.message}`, 'error');
    }
  }

  async function audition(id) {
    try {
      await ensureAudio();
      keeperVideo.pause();
      clearTransport();
      setActive(id === 'bed' ? 'bed-open' : id);
      const now = Tone.now();
      if (id === 'pulse') {
        trigger('pulse', now);
        setTimeout(() => setPlaying(false), 1100);
      } else if (id === 'tick') {
        trigger('tick', now);
        setTimeout(() => setPlaying(false), 850);
      } else if (id === 'reveal') {
        trigger('reveal', now);
        setTimeout(() => setPlaying(false), 1900);
      } else if (id === 'bed') {
        trigger('bed-open', now);
        trigger('bed-hold', now + 1.6);
        trigger('bed-resolve', now + 3.2);
        setTimeout(() => setActive(''), 5000);
      }
      setStatus(`Auditioning ${id} cue`, 'playing');
    } catch (error) {
      starting = false;
      setPlaying(false);
      setStatus(`Audio unavailable: ${error.message}`, 'error');
    }
  }

  playSketch.addEventListener('click', playCueSketch);
  keeperVideo.addEventListener('play', () => {
    clearTransport();
    Tone.getDraw().cancel();
    setPlaying(false);
    setStatus('Keeper video playing · Tone.js sketch stopped', 'ready');
  });
  stopSound.addEventListener('click', () => {
    clearTransport();
    Tone.getDraw().cancel();
    setPlaying(false);
    setStatus('Stopped · cue positions reset', 'ready');
  });
  presetButtons.forEach((button) => button.addEventListener('click', () => audition(button.dataset.audition)));
  volume.addEventListener('input', () => {
    if (built) master.volume.rampTo(Number(volume.value), .05);
  });

  if (!window.Tone) setStatus('Tone.js unavailable · check the local asset', 'error');

  window.RecastSoundLab = Object.freeze({
    version: '1.0.0',
    toneVersion: '15.1.22',
    cues,
    isReady: () => built,
    isPlaying: () => playing,
  });
})();
