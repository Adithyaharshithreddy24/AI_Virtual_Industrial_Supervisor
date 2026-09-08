import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import VoiceRecorder from './Components/Voice.jsx'
import Calls from './Components/Calls.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <VoiceRecorder />
    <Calls />
  </StrictMode>,
)
