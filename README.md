# Overview

This is a Facebook Messenger automation bot that sends automated messages to specific conversations using Facebook cookies for authentication. The application runs a simple HTTP server to maintain uptime (likely on Replit) while executing message-sending tasks in the background. The bot reads configuration from text files including cookies, conversation IDs, message content, hater names, and timing intervals.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure

**Single-File Python Application**
- The entire application logic resides in `main.py` with no modular separation
- Uses a monolithic approach with all functionality in one file
- **Rationale**: Simplicity for a small automation script; easier to deploy and debug on Replit
- **Cons**: Limited scalability and maintainability as features grow

## Web Server Component

**HTTP Server for Health Checks**
- Built-in Python `http.server` module running on a separate thread
- Responds with "Server is Running" to all GET requests
- Port configured via environment variable (defaults to 4000)
- **Purpose**: Keep the Replit instance alive by responding to health check pings
- **Rationale**: Replit requires active HTTP responses to prevent container sleep

## Authentication Mechanism

**Cookie-Based Facebook Authentication**
- Stores raw Facebook cookies in `cookies.txt` file
- Parses semicolon-separated cookie string into dictionary
- Requires critical cookies: `c_user` (user ID) and `xs` (session token)
- **Security Consideration**: No encryption or secure storage; cookies stored in plain text
- **Limitation**: Cookies expire and must be manually refreshed (documented in HOW_TO_FIX_COOKIES.md)

## Configuration Management

**File-Based Configuration System**
- `cookies.txt`: Facebook authentication cookies
- `convo.txt`: Target conversation/thread ID
- `hatersname.txt`: Message content or recipient identifier
- `time.txt`: Delay interval between messages (in seconds)
- `file.txt` / `File.txt`: Purpose unclear from codebase
- **Rationale**: Simple file-based config allows non-technical users to modify behavior without code changes
- **Alternative Considered**: Environment variables (more secure but less accessible)
- **Cons**: No validation, error-prone manual editing, security risks

## Message Sending Logic

**HTTP Request-Based Messaging** (Incomplete in provided code)
- Uses `requests` library to interact with Facebook's web endpoints
- Headers prepared for mimicking browser requests
- **Note**: Core sending logic appears truncated in the provided `main.py`
- **Expected Flow**: Parse cookies → Build authenticated request → POST message to Facebook API

## Threading Model

**Multi-Threaded Execution**
- HTTP server runs on dedicated thread via `threading` module
- Main thread handles message automation logic
- **Rationale**: Allows simultaneous HTTP server operation and message sending
- **Consideration**: No thread synchronization mechanisms visible (may not be needed for this simple use case)

## Error Handling

**Basic Error Detection**
- Cookie validation checks for required fields
- Debug logging for cookie parsing
- Try-except blocks for file operations
- **Limitation**: No retry logic, no graceful degradation, minimal user feedback

# External Dependencies

## Python Libraries

**requests (v2.31.0)**
- Purpose: HTTP client for Facebook API interactions
- Used for sending authenticated requests to Facebook endpoints
- Specified in `requirements.txt` (listed twice, likely an error)

**Standard Library Modules**
- `http.server` & `socketserver`: Built-in HTTP server
- `threading`: Concurrent execution
- `json`: Data parsing (imported but usage not visible in truncated code)
- `time`: Delays between message sends
- `random`: Likely for randomizing intervals or message variations
- `re`: Regular expressions (imported but usage not visible)

## Python Runtime

**Python 3.9.16**
- Specified in `runtime.txt` for Replit deployment
- Version pinning ensures consistent behavior across deployments

## External Services

**Facebook/Meta Platform**
- Direct web scraping/automation of facebook.com
- No official API usage (relies on cookie-based authentication)
- **Risk**: Violates Facebook Terms of Service; account suspension likely
- **Dependency**: Relies on Facebook's web interface remaining stable

## Hosting Platform

**Replit**
- Implied by server architecture (health check pattern, PORT environment variable)
- File-based configuration suitable for Replit's persistent storage
- **Consideration**: Free tier requires active HTTP responses to prevent sleep

## Missing Infrastructure

**No Database**
- All state stored in text files
- No message history, logging, or analytics persistence
- **Limitation**: Cannot track sent messages, errors, or usage patterns

**No Authentication/Authorization**
- No user access controls
- Anyone with Replit access can modify cookies and configuration
- **Security Risk**: Shared environments could expose Facebook credentials
