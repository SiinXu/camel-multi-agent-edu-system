import React, { useState, useEffect, useRef } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/outline';
import WaveSurfer from 'wavesurfer.js';

export function VoiceInput({ onVoiceResult, language = 'zh-CN' }) {
  const [isRecording, setIsRecording] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const recognition = useRef(null);
  const waveformRef = useRef(null);
  const wavesurfer = useRef(null);

  useEffect(() => {
    // Initialize WaveSurfer
    wavesurfer.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#4F46E5',
      progressColor: '#818CF8',
      cursorColor: '#C7D2FE',
      barWidth: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 50,
      barGap: 3
    });

    return () => wavesurfer.current.destroy();
  }, []);

  useEffect(() => {
    // Initialize speech recognition
    if (!('webkitSpeechRecognition' in window)) {
      console.error('Speech recognition not supported');
      return;
    }

    recognition.current = new window.webkitSpeechRecognition();
    recognition.current.continuous = true;
    recognition.current.interimResults = true;
    recognition.current.lang = language;

    recognition.current.onstart = () => {
      setIsRecording(true);
      // Start visualizing audio
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          const audioContext = new AudioContext();
          const source = audioContext.createMediaStreamSource(stream);
          const analyser = audioContext.createAnalyser();
          source.connect(analyser);
          // Update waveform visualization
          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const draw = () => {
            analyser.getByteTimeDomainData(dataArray);
            if (wavesurfer.current) {
              wavesurfer.current.loadDecodedBuffer(dataArray);
            }
            requestAnimationFrame(draw);
          };
          draw();
        });
    };

    recognition.current.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      onVoiceResult(finalTranscript, interimTranscript);
    };

    recognition.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };

    recognition.current.onend = () => {
      setIsRecording(false);
    };

    // Initialize speech synthesis voices
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices.filter(voice => voice.lang.startsWith(language.slice(0, 2))));
      if (voices.length > 0) {
        setSelectedVoice(voices[0]);
      }
    };

    window.speechSynthesis.onvoiceschanged = loadVoices;
    loadVoices();

    return () => {
      if (recognition.current) {
        recognition.current.stop();
      }
    };
  }, [language]);

  const handleStartStop = () => {
    if (isRecording) {
      recognition.current.stop();
    } else {
      recognition.current.start();
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center space-x-2">
        <button
          onClick={handleStartStop}
          className={`p-2 rounded-full transition-colors ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600'
          }`}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {isRecording ? (
            <StopIcon className="w-5 h-5" />
          ) : (
            <MicrophoneIcon className="w-5 h-5" />
          )}
        </button>
        {availableVoices.length > 0 && (
          <select
            value={selectedVoice?.name || ''}
            onChange={(e) => setSelectedVoice(availableVoices.find(v => v.name === e.target.value))}
            className="ml-2 p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
          >
            {availableVoices.map(voice => (
              <option key={voice.name} value={voice.name}>
                {voice.name}
              </option>
            ))}
          </select>
        )}
      </div>
      <div 
        ref={waveformRef} 
        className="w-full h-12 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden"
      />
    </div>
  );
}
