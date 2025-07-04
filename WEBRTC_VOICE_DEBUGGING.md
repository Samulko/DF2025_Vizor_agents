# WebRTC Voice Interface Debugging Guide

## Overview
This guide helps troubleshoot WebRTC connection issues when using the voice interface in the bridge design system. The most common symptom is clicking the "Record" button and getting a timeout without establishing a connection.

## Common Error Patterns

### 1. aioice Connection Logs
```
16:11:03 - aioice.ice - INFO - Connection(0) Check CandidatePair(('10.255.255.254', 57869) -> ('100.67.96.84', 62468)) State.FROZEN -> State.WAITING
16:11:03 - aioice.ice - INFO - Connection(0) Check CandidatePair(('100.67.96.84', 60113) -> ('100.67.96.84', 62468)) State.WAITING -> State.IN_PROGRESS
```
This indicates WebRTC candidate pairs are stuck in the connection negotiation phase.

### 2. Browser Console Errors
- `TypeError: Cannot read properties of undefined (reading 'getUserMedia')`
- `Cannot read properties of undefined (reading 'stop')`
- `NotAllowedError: Permission denied`
- `NotSecureError: Only secure origins are allowed`

## Step-by-Step Debugging

### Step 1: Check URL Access Method
**Issue**: Browser security restrictions prevent microphone access over HTTP when not using localhost.

**Test**:
```bash
# ✅ CORRECT - Use localhost
http://127.0.0.1:7860
http://localhost:7860

# ❌ WRONG - Will fail on most browsers
http://192.168.1.100:7860
http://YOUR_IP_ADDRESS:7860
```

**Fix**: Always use localhost/127.0.0.1 for local development.

### Step 2: Browser Security Check
**Test Browser Permissions**:
1. Open browser developer tools (F12)
2. Go to Console tab
3. Click "Record" button
4. Check for permission errors

**Common Issues**:
- Microphone blocked in browser settings
- Site permissions not granted
- Browser doesn't support WebRTC over HTTP

**Fix**:
1. Go to browser settings → Privacy & Security → Site Settings → Microphone
2. Ensure microphone is allowed for localhost
3. Try different browser (Chrome, Firefox, Edge)

### Step 3: Network Environment Check
**Corporate/School Networks**:
Many institutional networks block WebRTC traffic or have strict firewall rules.

**Test**:
```bash
# Test if running on restricted network
curl -I http://127.0.0.1:7860
```

**Fix**:
- Test on personal network/hotspot
- Contact network admin to allow WebRTC ports
- Use mobile hotspot as temporary workaround

### Step 4: HTTPS Alternative
**For Remote Access**:
If you need to access from another device, use Gradio's built-in sharing.

**Implementation**:
```python
# In your launch code, add share=True
interface.launch(share=True)
```

This creates a public HTTPS link that works with microphone access.

### Step 5: Process Architecture Check
**Verify Two-Terminal Setup**:
The system uses a two-terminal architecture for better reliability.

**Terminal 1 (Main System)**:
```bash
uv run python -m bridge_design_system.main --interactive --enable-command-server
```

**Terminal 2 (Voice Interface)**:
```bash
uv run python -m bridge_design_system.agents.chat_voice voice
```

**Test Connection**:
```bash
# Test IPC connection
python test_ipc_setup.py
```

## Advanced Debugging

### Check WebRTC Support
**Browser Test**:
```javascript
// Run in browser console
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => console.log('✅ Microphone access granted'))
  .catch(err => console.error('❌ Microphone access denied:', err));
```

### Check System Audio
**Linux/WSL**:
```bash
# Check audio devices
aplay -l
arecord -l

# Test microphone
arecord -f cd -t wav -d 5 test.wav
aplay test.wav
```

**Windows**:
```powershell
# Check audio devices in Device Manager
# Test microphone in Windows Sound settings
```

### Port Conflicts
**Check if ports are in use**:
```bash
# Check if Gradio port is available
netstat -tulpn | grep :7860

# Check if IPC port is available
netstat -tulpn | grep :8080
```

### Environment Variables
**Check voice configuration**:
```bash
# Verify .env file exists and has required keys
cat .env | grep -E "(ANTHROPIC_API_KEY|OPENAI_API_KEY|ACCESS_KEY)"
```

## Specific Solutions by Environment

### Student Lab/Classroom Setup
**Common Issues**:
- Restricted network access
- Shared computers with locked-down browsers
- Proxy servers blocking WebRTC

**Solutions**:
1. Use personal laptop with hotspot
2. Request network admin to whitelist WebRTC ports
3. Use offline mode if available

### Home/Personal Setup
**Common Issues**:
- Router firewall blocking WebRTC
- VPN interference
- Browser extensions blocking microphone

**Solutions**:
1. Disable VPN temporarily
2. Try incognito/private browsing mode
3. Check router settings for WebRTC blocking

### WSL2 Environment
**Special Considerations**:
- Audio passthrough issues
- Network interface conflicts
- Port forwarding problems

**Solutions**:
```bash
# Check WSL2 network interface
ip addr show

# Test localhost accessibility
curl http://127.0.0.1:7860
```

## Fallback Options

### 1. Keyboard Input Mode
If voice fails, fall back to keyboard input:
```bash
uv run python -m bridge_design_system.main --interactive
```

### 2. Alternative Voice Setup
Use the standalone voice assistant:
```bash
# In separate terminal
cd src/bridge_design_system/whisper-voice-assistant
python voice_assistant.py
```

### 3. Debug Mode
Enable verbose logging:
```bash
# Add debug flags
uv run python -m bridge_design_system.agents.chat_voice voice --debug
```

## Testing Checklist

Before deploying to students, verify:

- [ ] Works on localhost (127.0.0.1:7860)
- [ ] Browser permissions granted
- [ ] Microphone test in browser works
- [ ] Both terminals running correctly
- [ ] IPC connection established
- [ ] Test with different browsers
- [ ] Test on target network environment
- [ ] Fallback to keyboard input works

## Common Quick Fixes

1. **"Record button doesn't respond"**
   - Use localhost, not IP address
   - Check browser permissions

2. **"Connection timeout"**
   - Check network restrictions
   - Try different browser
   - Use mobile hotspot

3. **"No microphone detected"**
   - Check system audio settings
   - Test microphone in other apps
   - Verify browser has microphone access

4. **"Page won't load"**
   - Check both terminals are running
   - Verify port 7860 is available
   - Test with curl/browser refresh

## Getting Help

If issues persist:
1. Check browser console for specific errors
2. Run with debug flags for detailed logs
3. Test IPC connection independently
4. Verify system audio configuration
5. Try minimal test case with just Gradio WebRTC

Remember: Most WebRTC issues are browser security or network restrictions, not code problems.