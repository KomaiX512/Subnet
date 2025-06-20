# Miner Stage Tracking System

## Overview

This document describes the **Stage Tracking System** that provides transparent, real-time monitoring of content processing stages between `main.py` and `miner.py`. This system allows miner operators to see clean, user-friendly progress updates without being overwhelmed by internal debugging logs.

## Architecture

### Components

1. **`miner_stage_tracker.py`** - Core stage tracking library
2. **Enhanced `miner.py`** - Miner with integrated stage monitoring  
3. **Enhanced `main.py`** - Main processing with minimal stage reporting calls

### Stage Definitions

| Stage | Name | Description |
|-------|------|-------------|
| 0 | Initialization | System startup, module launching, watchdog setup |
| 1 | Data Scraping | Social media data collection from platforms |
| 2 | Data Retrieval | Processing and cleaning raw scraped data |
| 3 | Vector Database | Indexing posts and building embeddings |
| 4 | Time Series Analysis | Analyzing engagement patterns and trends |
| 5 | Content Generation | Creating content recommendations |
| 6 | Exportation | Saving final results and content plans |
| 7 | Complete | Pipeline completed successfully |

## Operation Modes

### 1. Watchdog Mode (Default)
- **Trigger**: Miner starts automatically in watchdog mode
- **Behavior**: Monitors for AccountInfo files, processes accounts as they appear
- **Stage Flow**: 
  ```
  Stage 0: "Watchdog mode initialized" 
       ↓
  Stage 0: "Waiting for accounts..." (when no accounts found)
       ↓  
  Stage 1: "Processing [platform] account with fresh scraping" (when account found)
       ↓
  Stages 2-7: Normal processing pipeline
  ```

### 2. Direct Processing Mode  
- **Trigger**: When `main.py` is called with specific username arguments
- **Behavior**: Processes specified account immediately
- **Stage Flow**:
  ```
  Stage 0: "Direct processing mode for [platform] account: [username]"
       ↓
  Stage 1: "Force fresh scraping for [username]" (if --force-fresh)
       ↓  
  Stages 2-7: Normal processing pipeline
  ```

## Miner Logging Examples

### Successful Processing
```
[INFO] 🚀 Content Recommendation Miner started successfully
[INFO] 🎯 Stage tracking system initialized  
[INFO] 📋 Starting Module 1: Content recommendation system
[INFO] 📋 Starting Module 2: Image generator and query handler
[INFO] ⚙️  Stage 0 - Initialization: Starting watchdog mode
[INFO] ✅ Stage 0 Complete - Initialization - Watchdog mode initialized successfully
[INFO] ⚙️  Stage 1 - Data Scraping for elonmusk: Processing twitter account with fresh scraping  
[INFO] ✅ Stage 1 Complete - Data Scraping for elonmusk - Successfully processed twitter account
[INFO] ⚙️  Stage 2 - Data Retrieval for elonmusk: Processing and validating data
[INFO] ✅ Stage 2 Complete - Data Retrieval for elonmusk - Data validation successful
[INFO] ⚙️  Stage 3 - Vector Database for elonmusk: Indexing 50 posts in vector database
[INFO] ✅ Stage 3 Complete - Vector Database for elonmusk - Successfully indexed posts in vector database
[INFO] ⚙️  Stage 4 - Time Series Analysis for elonmusk: Analyzing engagement data and patterns
[INFO] ✅ Stage 4 Complete - Time Series Analysis for elonmusk - Successfully analyzed engagement data
[INFO] ⚙️  Stage 5 - Content Generation for elonmusk: Generating content recommendations
[INFO] ✅ Stage 5 Complete - Content Generation for elonmusk - Successfully generated content recommendations
[INFO] ⚙️  Stage 6 - Exportation for elonmusk: Exporting content plan and results  
[INFO] ✅ Stage 6 Complete - Exportation for elonmusk - Successfully exported content plan
[INFO] ✅ Stage 7 Complete - Complete for elonmusk - Pipeline completed - 15 recommendations generated
```

### Failure Scenario
```
[INFO] ⚙️  Stage 1 - Data Scraping for badusername: Processing twitter account with fresh scraping
[ERROR] ❌ Stage 1 Failed - Data Scraping for badusername - Error: Failed to scrape profile
[INFO] ⚙️  Stage 0 - Initialization: Waiting for accounts to process
```

### Watchdog Waiting
```
[INFO] ⚙️  Stage 0 - Initialization: No accounts found - waiting 300 seconds for new accounts
[INFO] ✅ Stage 0 Complete - Initialization - Wait cycle completed - checking for new accounts
```

## Miner Status Reporting

The miner provides periodic status updates every 30 seconds:

```
[INFO] 📈 Miner Status: Mode: watchdog | Module 1: Running | Module 2: Running | Stage: Vector Database - running (elonmusk)
```

## Technical Implementation

### File-Based Communication
- **Status File**: `miner_status.json` (created automatically)
- **Thread-Safe**: Uses file locking for concurrent access
- **Non-Blocking**: Stage tracking failures don't disrupt main processing
- **Self-Healing**: Missing modules gracefully degrade to no-op functions

### Stage Tracking API

```python
# In main.py - minimal integration calls
stage_start(stage_number, "Description", username="", details={})
stage_complete(stage_number, "Success message", username="", details={})  
stage_failed(stage_number, "Error message", username="", details={})

# In miner.py - monitoring setup
reporter = MinerStageReporter(get_tracker(), bt.logging)
reporter.start_monitoring(check_interval=1.0)
```

### Error Handling
- **Graceful Degradation**: If stage tracking unavailable, continues without logging
- **No-Op Functions**: Missing imports automatically create dummy functions
- **Silent Failures**: Stage tracking errors don't affect main processing
- **Module Recovery**: Automatically restarts crashed modules

## Benefits

### For Miner Operators
- **Clear Progress Visibility**: Know exactly what stage processing is in
- **User-Friendly Logging**: Clean messages without overwhelming debug info
- **Real-Time Monitoring**: See progress as it happens
- **Error Transparency**: Clear indication when and where failures occur
- **Dual Module Tracking**: Monitor both content processing and image generation

### For Developers  
- **Non-Intrusive**: Minimal changes to existing codebase
- **Robust**: Designed to never break existing functionality
- **Extensible**: Easy to add new stages or modify reporting
- **Testable**: Comprehensive test suite for verification

## Configuration

### Stage Monitoring Interval
```python
# In miner.py
reporter.start_monitoring(check_interval=1.0)  # Check every 1 second
```

### Miner Status Update Frequency
```python  
# In miner.py main loop
time.sleep(30)  # Update status every 30 seconds
```

## File Structure

```
├── Miners/
│   ├── main.py                     # Enhanced with stage tracking calls
│   ├── miner_stage_tracker.py      # Core stage tracking library
│   └── Module2/                    # Image generator module
├── neurons/
│   └── miner.py                    # Enhanced with stage monitoring
└── test_stage_tracking.py          # Test suite
```

## Testing

Run the test suite to verify stage tracking:

```bash
python test_stage_tracking.py
```

Expected output shows all stages progressing through their lifecycle with proper success/failure reporting.

## Troubleshooting

### Stage Tracking Not Working
1. Verify `miner_stage_tracker.py` exists in `Miners/` directory
2. Check Python path includes `Miners/` directory  
3. Look for import errors in miner startup logs

### Modules Not Starting
1. Check file paths in miner initialization
2. Verify `main.py` and `Module2/main.py` exist
3. Review module health check logs for restart attempts

### Missing Stage Updates
1. Confirm stage tracking calls exist in processing pipeline
2. Check file permissions for `miner_status.json`
3. Verify monitoring thread is running (look for "Stage monitoring activated")

## Future Enhancements

- Stage duration tracking and performance metrics
- Web dashboard for remote monitoring
- Integration with Bittensor validator reporting
- Custom stage definitions for different processing types
- Historical stage performance analytics 