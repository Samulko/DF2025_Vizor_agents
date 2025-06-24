# Gaze Integration Testing Guide

This guide explains how to test the HoloLens gaze integration using the existing test infrastructure.

## Prerequisites

1. **ROS Bridge Server**: Must be running on `localhost:9090`
2. **Python Dependencies**: `roslibpy` installed
3. **Bridge Design System**: Properly configured and importable

## Test Infrastructure

### Existing Test Scripts

#### `tests/vizor_connection/send_gaze.py`
- **Purpose**: Simulates HoloLens gaze data by sending ROS messages
- **Usage**: `python tests/vizor_connection/send_gaze.py <element_id>`
- **Example**: `python tests/vizor_connection/send_gaze.py 003`
- **Output**: Sends `dynamic_003` to `/HOLO1_GazePoint` topic

#### `tests/vizor_connection/send_transform.py`
- **Purpose**: Simulates HoloLens transform data
- **Usage**: `python tests/vizor_connection/send_transform.py <t1|t2>`
- **Note**: Used for testing transform features (not core gaze functionality)

### New Integration Test

#### `tests/test_gaze_integration.py`
- **Purpose**: Comprehensive gaze integration testing
- **Features**:
  - VizorListener connection validation
  - Gaze data capture testing
  - Spatial vs non-spatial command routing
  - Single-shot policy validation
  - Error handling verification

## Manual Testing Workflow

### 1. Basic Gaze Detection Test

```bash
# Terminal 1: Start the main application
python -m src.bridge_design_system.main --interactive

# Terminal 2: Send gaze data
python tests/vizor_connection/send_gaze.py 001

# Terminal 1: Issue spatial command
Designer> move this element
# Should see: [Debug] Gaze detected on: dynamic_001
# Should route to geometry agent with gaze context
```

### 2. Spatial Command Detection Test

```bash
# Send gaze data
python tests/vizor_connection/send_gaze.py 002

# Test spatial commands (should use gaze):
Designer> move this element
Designer> modify that component  
Designer> edit this script
Designer> select this object

# Test non-spatial commands (should ignore gaze):
Designer> what is the material status?
Designer> list available agents
Designer> show me the system status
```

### 3. Single-Shot Policy Test

```bash
# Send gaze data
python tests/vizor_connection/send_gaze.py 003

# Issue first command
Designer> move this element
# Should see gaze detection and processing

# Issue second command immediately (no new gaze data)
Designer> move this element  
# Should NOT see gaze detection (cleared after first command)
# Should ask for clarification
```

### 4. Element ID Mapping Test

```bash
# Test different element IDs
python tests/vizor_connection/send_gaze.py 001  # → dynamic_001 → component_1
python tests/vizor_connection/send_gaze.py 020  # → dynamic_020 → component_20
python tests/vizor_connection/send_gaze.py 123  # → dynamic_123 → component_123

# Each should correctly map to the corresponding component
```

### 5. Error Handling Test

```bash
# Test with invalid element ID format
# (manually modify send_gaze.py to send "invalid_format")

Designer> move this element
# Should gracefully handle invalid gaze data
# Should proceed without gaze context
```

## Automated Testing

### Run Complete Test Suite

```bash
# Ensure ROS bridge is running
# Then run the automated test suite
python tests/test_gaze_integration.py
```

**Expected Output:**
```
🚀 Starting Gaze Integration Test Suite
==================================================
🔧 Setting up gaze integration test harness...
📡 Initializing VizorListener...
✅ VizorListener connected to ROS bridge
🎯 Initializing triage system...
✅ Triage system initialized

🔍 Test 1: Gaze Data Capture
----------------------------------------
📤 Sending gaze message for element: 003
✅ Gaze message sent successfully
✅ Gaze capture successful: dynamic_003

🎯 Test 2: Spatial Command Routing
----------------------------------------
📤 Sending gaze message for element: 001
✅ Gaze message sent successfully
📍 Current gaze: dynamic_001
🔄 Testing spatial command: 'move this element'
✅ Spatial command processed successfully

... (additional tests)

📊 Test Results Summary
==================================================
✅ Gaze Data Capture: PASS
✅ Spatial Command Routing: PASS
✅ Non-Spatial Command Routing: PASS
✅ Single-Shot Policy: PASS
✅ Invalid Gaze Handling: PASS

Passed: 5/5 tests
🎉 All tests passed! Gaze integration is working correctly.
```

## Troubleshooting

### Common Issues

1. **ROS Connection Failed**
   ```
   ❌ ROS connection failed - make sure ROS bridge is running on localhost:9090
   ```
   **Solution**: Start ROS bridge server before testing

2. **Import Errors**
   ```
   ❌ Failed to import bridge design system components
   ```
   **Solution**: Run tests from project root directory

3. **Gaze Data Not Detected**
   ```
   ❌ Gaze capture failed. Expected: dynamic_003, Got: None
   ```
   **Solution**: Check ROS topic publishing and VizorListener subscription

4. **Invalid Gaze Format**
   ```
   ⚠️ Invalid gaze ID format ignored: invalid_gaze
   ```
   **Solution**: Ensure gaze IDs follow `dynamic_XXX` format

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('bridge_design_system').setLevel(logging.DEBUG)
```

## Integration with CI/CD

For automated testing in CI/CD pipelines:

```bash
# Start ROS bridge server (if available)
# Run gaze integration tests
python tests/test_gaze_integration.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Gaze integration tests passed"
else
    echo "❌ Gaze integration tests failed"
    exit 1
fi
```

## Performance Testing

### Latency Testing

Measure gaze-to-action latency:

```python
import time

start_time = time.time()
# Send gaze message
subprocess.run([sys.executable, "tests/vizor_connection/send_gaze.py", "001"])
# Process command
response = triage.handle_design_request("move this element", gaze_id="dynamic_001")
end_time = time.time()

latency = (end_time - start_time) * 1000  # ms
print(f"Gaze-to-action latency: {latency:.2f}ms")
```

### Load Testing

Test multiple rapid gaze changes:

```bash
for i in {001..010}; do
    python tests/vizor_connection/send_gaze.py $i
    sleep 0.1
done
```

This comprehensive testing approach ensures the gaze integration works correctly in all scenarios and maintains the quality and reliability of the Bridge Design System.